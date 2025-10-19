<script>
  import Lobby from './components/Lobby.svelte';
  import Table from './components/Table.svelte';
  import { currentTable } from './lib/store.js';
</script>

<main>
  {#if $currentTable}
    <Table />
  {:else}
    <Lobby />
  {/if}
</main>
