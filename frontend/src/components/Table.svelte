<script>
  import { tableState, user, socket } from '../lib/store.js';
  import { fade, fly, scale } from 'svelte/transition';
  import { quintOut } from 'svelte/easing';

  function sendAction(action, amount=0) {
    console.log('sendAction called:', action, amount);
    console.log('Socket state:', $socket);
    console.log('User state:', $user);
    
    if ($socket && $socket.readyState === WebSocket.OPEN) {
      const message = {
        type: 'action',
        action,
        amount,
        player_id: $user.id,
        table_id: $user.table_id
      };
      console.log('Sending message:', message);
      $socket.send(JSON.stringify(message));
    } else {
      console.error('WebSocket not connected!', $socket?.readyState);
    }
  }
  
  // Reactive state
  $: pot = $tableState?.pot || 0;
  $: community_cards = $tableState?.community_cards || [];
  $: players = $tableState?.players || [];
  $: phase = $tableState?.phase || 'waiting';
  $: current_turn_index = $tableState?.current_turn_index;
  $: dealer_index = $tableState?.dealer_index;
  
  // Winner notification
  let showWinner = false;
  let winnerName = '';
  let winnerAmount = 0;
  
  // Timer
  let timeLeft = 30;
  let timerInterval = null;
  
  // Watch for state updates to detect winner
  $: if ($tableState) {
    // Reset timer when turn changes
    if (current_turn_index !== undefined) {
      resetTimer();
    }
  }
  
  function resetTimer() {
    timeLeft = 30;
    if (timerInterval) clearInterval(timerInterval);
    timerInterval = setInterval(() => {
      timeLeft--;
      if (timeLeft <= 0) {
        clearInterval(timerInterval);
        // Auto-fold when timer expires (if it's my turn)
        const myPlayer = players.find(p => p.id === $user?.id);
        const myIndex = players.findIndex(p => p.id === $user?.id);
        if (myIndex === current_turn_index) {
          sendAction('fold');
        }
      }
    }, 1000);
  }
  
  // Listen for winner in WebSocket messages
  import { onMount, onDestroy } from 'svelte';
  
  onMount(() => {
    if ($socket) {
      const originalOnMessage = $socket.onmessage;
      $socket.onmessage = (event) => {
        originalOnMessage(event);
        const data = JSON.parse(event.data);
        // Check for showdown event in events array
        if (data.events) {
          const showdownEvent = data.events.find(e => e.type === 'showdown');
          if (showdownEvent) {
            const winner = players.find(p => p.id === showdownEvent.winner_id);
            if (winner) {
              winnerName = winner.username;
              winnerAmount = showdownEvent.amount;
              showWinner = true;
              setTimeout(() => { showWinner = false; }, 5000);
            }
          }
        }
      };
    }
  });
  
  onDestroy(() => {
    if (timerInterval) clearInterval(timerInterval);
  });
  
  function isMyTurn(player, index) {
      return index === current_turn_index;
  }
  
  function displayRank(rank) {
    return rank === 'T' ? '10' : rank;
  }

</script>

<div class="flex flex-col h-screen bg-green-800 text-white p-4 overflow-hidden relative">
  <!-- Header -->
  <div class="flex justify-between items-center mb-4 z-10">
    <div class="bg-black/40 px-4 py-2 rounded-lg backdrop-blur-sm">
        <h2 class="text-xl font-bold text-gray-200">Table: {$user?.table_id}</h2>
        <div class="text-sm text-gray-400 uppercase tracking-wider">{phase}</div>
    </div>
    <div class="flex items-center space-x-4">
      <div class="text-2xl font-bold bg-black/50 px-6 py-3 rounded-full border border-yellow-500/30 shadow-lg text-yellow-400">
          Pot: ${pot}
      </div>
      {#if current_turn_index !== null && current_turn_index !== undefined}
        <div class="text-lg font-bold px-4 py-2 rounded-full border-2 shadow-lg" 
             class:bg-green-600={timeLeft > 10}
             class:bg-yellow-600={timeLeft <= 10 && timeLeft > 5}
             class:bg-red-600={timeLeft <= 5}
             class:border-green-400={timeLeft > 10}
             class:border-yellow-400={timeLeft <= 10 && timeLeft > 5}
             class:border-red-400={timeLeft <= 5}>
          ⏱️ {timeLeft}s
        </div>
      {/if}
    </div>
  </div>

  <div class="flex-grow flex flex-col items-center justify-center relative">
    
    <!-- Community Cards -->
    <div class="flex space-x-3 mb-12 h-32 items-center justify-center">
      {#each community_cards as card, i (card.rank + card.suit)}
        <div 
            in:fly={{ y: -50, duration: 600, delay: i * 200, easing: quintOut }}
            class="w-20 h-28 bg-white text-black rounded-lg flex flex-col items-center justify-center font-bold text-2xl border-2 border-gray-300 shadow-2xl transform hover:scale-110 transition-transform duration-200"
        >
          <span class={['h','d'].includes(card.suit) ? 'text-red-600' : 'text-black'}>
            {displayRank(card.rank)}
          </span>
          <span class={['h','d'].includes(card.suit) ? 'text-red-600 text-3xl' : 'text-black text-3xl'}>
            {card.suit === 'h' ? '♥' : card.suit === 'd' ? '♦' : card.suit === 'c' ? '♣' : '♠'}
          </span>
        </div>
      {/each}
      {#if community_cards.length === 0}
        <div class="text-white/30 italic font-light tracking-widest" in:fade>WAITING FOR DEAL...</div>
      {/if}
    </div>

    <!-- Players -->
    <div class="grid grid-cols-3 gap-12 w-full max-w-5xl px-8">
        {#each players as player, i (player.id)}
            <div 
                class="relative flex flex-col items-center p-4 rounded-xl transition-all duration-300 
                {isMyTurn(player, i) ? 'bg-yellow-500/20 border-2 border-yellow-400 shadow-[0_0_20px_rgba(250,204,21,0.3)] scale-105' : 'bg-black/40 border border-white/10'}
                {player.has_folded ? 'opacity-50 grayscale' : ''}"
            >
                <!-- Dealer Button -->
                {#if i === dealer_index}
                    <div class="absolute -top-3 -right-3 w-8 h-8 bg-white text-black rounded-full flex items-center justify-center font-bold border-2 border-gray-400 shadow-md z-20">D</div>
                {/if}

                <div class="font-bold text-lg mb-1">{player.username}</div>
                <div class="text-green-400 font-mono bg-black/30 px-2 rounded">${player.chips}</div>
                
                {#if player.current_bet > 0}
                    <div class="mt-2 text-yellow-300 text-sm font-bold bg-yellow-900/50 px-2 py-1 rounded-full flex items-center">
                        <span class="mr-1">🪙</span> ${player.current_bet}
                    </div>
                {/if}

                <!-- Hole Cards -->
                {#if player.hole_cards && player.id === $user.id}
                    <div class="flex space-x-2 mt-3 absolute -bottom-16">
                        {#each player.hole_cards as card}
                            <div class="w-14 h-20 bg-white text-black text-lg flex flex-col items-center justify-center rounded border border-gray-400 shadow-xl">
                                <span class={['h','d'].includes(card.suit) ? 'text-red-600' : 'text-black'}>{displayRank(card.rank)}</span>
                                <span class={['h','d'].includes(card.suit) ? 'text-red-600' : 'text-black'}>{card.suit === 'h' ? '♥' : card.suit === 'd' ? '♦' : card.suit === 'c' ? '♣' : '♠'}</span>
                            </div>
                        {/each}
                    </div>
                {:else if !player.has_folded && phase !== 'waiting'}
                     <!-- Card Backs for opponents -->
                    <div class="flex space-x-1 mt-3 opacity-80">
                        <div class="w-10 h-14 bg-blue-900 rounded border border-white/20"></div>
                        <div class="w-10 h-14 bg-blue-900 rounded border border-white/20"></div>
                    </div>
                {/if}
                
                {#if player.has_folded}
                    <div class="absolute inset-0 flex items-center justify-center bg-black/60 rounded-xl">
                        <span class="text-red-500 font-bold transform -rotate-12 border-2 border-red-500 px-2 py-1 rounded">FOLD</span>
                    </div>
                {/if}
            </div>
        {/each}
    </div>
  </div>

  <!-- Winner Notification -->
  {#if showWinner}
    <div class="absolute inset-0 flex items-center justify-center bg-black/70 z-50" transition:fade>
      <div class="bg-gradient-to-br from-yellow-400 to-yellow-600 p-8 rounded-2xl shadow-2xl border-4 border-yellow-300 transform scale-110" in:scale={{ duration: 500 }}>
        <div class="text-center">
          <div class="text-6xl mb-4">🏆</div>
          <h2 class="text-4xl font-bold text-gray-900 mb-2">{winnerName} Wins!</h2>
          <p class="text-2xl font-bold text-gray-800">${winnerAmount}</p>
        </div>
      </div>
    </div>
  {/if}

  <!-- Controls -->
  <div class="bg-gray-900/90 backdrop-blur-md p-6 rounded-t-2xl flex justify-center space-x-6 shadow-2xl border-t border-white/10 z-20">
    <button on:click={() => sendAction('fold')} class="bg-red-600 hover:bg-red-500 px-8 py-3 rounded-lg font-bold transition transform hover:-translate-y-1 shadow-lg shadow-red-900/50">Fold</button>
    <button on:click={() => sendAction('check')} class="bg-yellow-600 hover:bg-yellow-500 px-8 py-3 rounded-lg font-bold transition transform hover:-translate-y-1 shadow-lg shadow-yellow-900/50">Check</button>
    <button on:click={() => sendAction('call')} class="bg-blue-600 hover:bg-blue-500 px-8 py-3 rounded-lg font-bold transition transform hover:-translate-y-1 shadow-lg shadow-blue-900/50">Call</button>
    <div class="flex space-x-2">
        <button on:click={() => sendAction('raise', 100)} class="bg-green-600 hover:bg-green-500 px-8 py-3 rounded-lg font-bold transition transform hover:-translate-y-1 shadow-lg shadow-green-900/50">Raise 100</button>
        <!-- Add slider or input for raise amount here in future -->
    </div>
  </div>
</div>
