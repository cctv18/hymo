<script>
  import { store } from '../lib/store.svelte';
  import { ICONS } from '../lib/constants';
  import { onMount } from 'svelte';
  import './ModulesTab.css';

  let searchQuery = $state('');
  let filterType = $state('all'); // all, auto, magic

  onMount(() => {
    store.loadModules();
  });

  // Derived state for filtering modules
  let filteredModules = $derived(store.modules.filter(m => {
    const q = searchQuery.toLowerCase();
    const matchSearch = m.name.toLowerCase().includes(q) || m.id.toLowerCase().includes(q);
    const matchFilter = filterType === 'all' || m.mode === filterType;
    return matchSearch && matchFilter;
  }));
</script>

<div class="md3-card" style="padding: 16px;">
  <p style="margin: 0; font-size: 14px; color: var(--md-sys-color-on-surface-variant); line-height: 1.5;">
    {store.L.modules.desc}
  </p>
</div>

<div class="search-container">
  <svg class="search-icon" viewBox="0 0 24 24"><path d={ICONS.search} /></svg>
  <input 
    type="text" 
    class="search-input" 
    placeholder={store.L.modules.searchPlaceholder}
    bind:value={searchQuery}
  />
  <div class="filter-controls">
    <span style="font-size: 12px; color: var(--md-sys-color-on-surface-variant);">{store.L.modules.filterLabel}</span>
    <select class="filter-select" bind:value={filterType}>
      <option value="all">{store.L.modules.filterAll}</option>
      <option value="auto">{store.L.modules.modeAuto}</option>
      <option value="magic">{store.L.modules.modeMagic}</option>
    </select>
  </div>
</div>

{#if store.loading.modules}
  <div style="text-align:center; padding: 40px; opacity: 0.6">
    {store.L.modules.scanning}
  </div>
{:else if filteredModules.length === 0}
  <div style="text-align:center; padding: 40px; opacity: 0.6">
    {store.modules.length === 0 ? store.L.modules.empty : "No matching modules"}
  </div>
{:else}
  <div class="rules-list">
    {#each filteredModules as mod (mod.id)}
      <div class="rule-card">
        <div class="rule-info">
          <div style="display:flex; flex-direction:column;">
            <span class="module-name">{mod.name}</span>
            <span class="module-id">{mod.id}</span>
          </div>
        </div>
        <div class="text-field" style="margin-bottom:0; width: 140px; flex-shrink: 0;">
          <select bind:value={mod.mode}>
            <option value="auto">{store.L.modules.modeAuto}</option>
            <option value="magic">{store.L.modules.modeMagic}</option>
          </select>
        </div>
      </div>
    {/each}
  </div>
{/if}

<div class="bottom-actions">
  <button class="btn-tonal" onclick={() => store.loadModules()} disabled={store.loading.modules} title={store.L.modules.reload}>
    <svg viewBox="0 0 24 24" width="20" height="20"><path d={ICONS.refresh} fill="currentColor"/></svg>
  </button>
  <button class="btn-filled" onclick={() => store.saveModules()} disabled={store.saving.modules}>
    <svg viewBox="0 0 24 24" width="18" height="18"><path d={ICONS.save} fill="currentColor"/></svg>
    {store.saving.modules ? store.L.common.saving : store.L.modules.save}
  </button>
</div>