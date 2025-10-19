<script>
  import { user, currentTable, connectWebSocket } from '../lib/store.js';

  let username = '';
  let tableId = 'Table1';
  let error = '';
  let joining = false;

  async function join() {
    if (!username || !tableId) {
      error = 'Please enter both username and table ID';
      return;
    }
    
    if (joining) return;
    joining = true;
    error = '';
    
    try {
      console.log('Joining table...', username, tableId);
      
      // Set user state
      user.set({ username, id: 'p-' + username, chips: 1000, table_id: tableId });
      
      // Connect WebSocket (returns promise)
      const ws = await connectWebSocket(tableId);
      
      console.log('WebSocket connected, sending join action');
      
      // Send join action via WebSocket
      ws.send(JSON.stringify({
        type: 'action',
        action: 'join',
        player_id: 'p-' + username,
        username: username,
        buyin: 1000,
        table_id: tableId
      }));
      
      console.log('Join action sent, switching to table view');
      
      // Switch to table view
      currentTable.set(tableId);
      
    } catch (e) {
      console.error("Failed to join", e);
      error = e.message || 'Failed to connect. Is the server running?';
      user.set(null);
      joining = false;
    }
  }
</script>

<div class="flex flex-col items-center justify-center h-screen bg-gray-900 text-white font-sans">
  <h1 class="text-5xl font-extrabold mb-12 text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-600">Poker Royale</h1>
  <div class="bg-gray-800 p-10 rounded-2xl shadow-2xl w-full max-w-md border border-gray-700">
    <div class="mb-6">
      <label class="block mb-2 text-gray-400 text-sm font-bold uppercase tracking-wider">Username</label>
      <input bind:value={username} class="w-full p-3 rounded bg-gray-700 border border-gray-600 text-white focus:outline-none focus:border-blue-500 transition" placeholder="Enter your name" />
    </div>
    <div class="mb-8">
      <label class="block mb-2 text-gray-400 text-sm font-bold uppercase tracking-wider">Table ID</label>
      <input bind:value={tableId} class="w-full p-3 rounded bg-gray-700 border border-gray-600 text-white focus:outline-none focus:border-blue-500 transition" placeholder="Enter table ID" />
    </div>
    <button on:click={join} disabled={joining} class="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-bold py-3 px-4 rounded-lg transform hover:scale-105 transition duration-200 shadow-lg disabled:opacity-50 disabled:cursor-not-allowed">
      {joining ? 'Joining...' : 'Join Table'}
    </button>
    {#if error}
      <p class="mt-4 text-red-400 text-sm text-center">{error}</p>
    {/if}
  </div>
</div>
