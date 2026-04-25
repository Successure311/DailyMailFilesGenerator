let marginData = {};
let tradeCountData = {};
let expectancyData = {};
let clientMarginData = [];
let allDates = [];
let selectedDate = '';
let strategyExpectancy = {};
let clientMarginList = [];

async function loadData() {
    const response = await fetch('/get_data');
    const data = await response.json();
    
    marginData = data.INDEX_MARGIN_DATA;
    tradeCountData = data.STRATEGY_TRADE_COUNT;
    expectancyData = data.STRATEGY_EXPECTANCY;
    strategyExpectancy = data.STRATEGY_EXPECTANCY;
    clientMarginData = data.CLIENT_MARGIN_DATA || [];
    clientMarginList = data.CLIENT_MARGIN_DATA || [];
    allDates = data.ALL_DATES || [];

    const clientOrder = ['OWN', 'MOSTI23482', 'MOSTI23035', 'SAT2484', 'MOSTI22960', 'MOSTI23372','MOSTI23422', 'MOSTI23461', 'MOSTI22967', 'MOSTI23395', 'MOSTI22962', 'MOSTI23247', 'H46524'];
    const orderMap = Object.fromEntries(clientOrder.map((c, i) => [c, i]));
    const sortFn = (a, b) => {
        const idxA = orderMap[a.ClientID];
        const idxB = orderMap[b.ClientID];
        if (idxA !== undefined && idxB !== undefined) return idxA - idxB;
        if (idxA !== undefined) return -1;
        if (idxB !== undefined) return 1;
        return a.ClientID.localeCompare(b.ClientID);
    };
    clientMarginData.sort(sortFn);
    clientMarginList.sort(sortFn);
    
    renderMarginTable();
    renderTradeCountTable();
    calculateExpectancy();
    renderClientMarginTable();
    renderDateDropdown();
}

function renderMarginTable() {
    const tbody = document.querySelector('#marginTable tbody');
    tbody.innerHTML = '';
    
    if (!marginData._rows) {
        marginData._rows = [];
        Object.keys(marginData).forEach(index => {
            if (index === '_rows') return;
            Object.keys(marginData[index] || {}).forEach(dayType => {
                const margin = marginData[index][dayType];
                if (margin && typeof margin === 'object') {
                    const dayTypeText = dayType === 'Non_Expiry' ? 'N.Expiry' : dayType;
                    marginData._rows.push({
                        index: index,
                        dayType: dayTypeText,
                        With_Hedge: margin.With_Hedge || 0,
                        Without_Hedge: margin.Without_Hedge || 0
                    });
                }
            });
        });
    }
    
    marginData._rows.forEach((rowData, idx) => {
        const row = document.createElement('tr');
        row.dataset.rowIdx = idx;
        row.innerHTML = `
            <td><input type="text" value="${rowData.index || ''}" class="index-input" data-row-idx="${idx}"></td>
            <td><input type="text" value="${rowData.dayType || ''}" class="daytype-input" data-row-idx="${idx}"></td>
            <td><input type="number" value="${rowData.With_Hedge || 0}" class="with-hedge" data-row-idx="${idx}"></td>
            <td><input type="number" value="${rowData.Without_Hedge || 0}" class="without-hedge" data-row-idx="${idx}"></td>
            <td><button class="btn btn-sm btn-danger py-0" onclick="removeMarginRow(this)">×</button></td>
        `;
        tbody.appendChild(row);
    });
    
    document.querySelectorAll('#marginTable input').forEach(el => {
        el.addEventListener('change', updateMarginData);
    });
}

function addMarginRow() {
    if (!marginData._rows) marginData._rows = [];
    marginData._rows.push({ index: 'INDEX', dayType: 'NEW', With_Hedge: 0, Without_Hedge: 0 });
    renderMarginTable();
}

function removeMarginRow(btn) {
    const row = btn.closest('tr');
    const idx = parseInt(row.dataset.rowIdx);
    
    if (!isNaN(idx)) {
        marginData._rows.splice(idx, 1);
    }
    renderMarginTable();
}

function updateMarginData(e) {
    const row = e.target.closest('tr');
    const idx = parseInt(row.dataset.rowIdx);
    
    if (!isNaN(idx)) {
        marginData._rows[idx].index = row.querySelector('.index-input').value;
        marginData._rows[idx].dayType = row.querySelector('.daytype-input').value;
        marginData._rows[idx].With_Hedge = parseInt(row.querySelector('.with-hedge').value) || 0;
        marginData._rows[idx].Without_Hedge = parseInt(row.querySelector('.without-hedge').value) || 0;
        calculateExpectancy();
    }
}

function renderTradeCountTable() {
    const tbody = document.querySelector('#tradeCountTable tbody');
    tbody.innerHTML = '';
    
    if (!tradeCountData._rows) {
        tradeCountData._rows = [];
        const allStrategies = new Set();
        Object.keys(tradeCountData).forEach(idx => {
            if (idx === '_rows') return;
            Object.keys(tradeCountData[idx] || {}).forEach(s => allStrategies.add(s));
        });
        allStrategies.forEach(strategy => {
            tradeCountData._rows.push({
                strategy: strategy,
                SENSEX: tradeCountData['SENSEX']?.[strategy] || '-',
                BANKNIFTY: tradeCountData['BANKNIFTY']?.[strategy] || '-',
                NIFTY: tradeCountData['NIFTY']?.[strategy] || '-'
            });
        });
    }
    
    tradeCountData._rows.forEach((rowData, idx) => {
        const row = document.createElement('tr');
        row.dataset.rowIdx = idx;
        row.innerHTML = `
            <td><input type="text" value="${rowData.strategy || ''}" class="strategy-input" data-row-idx="${idx}"></td>
            <td><input type="text" value="${rowData.SENSEX || '-'}" class="sensex-input" data-row-idx="${idx}"></td>
            <td><input type="text" value="${rowData.BANKNIFTY || '-'}" class="banknifty-input" data-row-idx="${idx}"></td>
            <td><input type="text" value="${rowData.NIFTY || '-'}" class="nifty-input" data-row-idx="${idx}"></td>
            <td><button class="btn btn-sm btn-danger py-0" onclick="removeTradeCountRow(this)">×</button></td>
        `;
        tbody.appendChild(row);
    });
    
    document.querySelectorAll('#tradeCountTable input').forEach(el => {
        el.addEventListener('change', updateTradeCount);
    });
}

function addTradeCountRow() {
    if (!tradeCountData._rows) tradeCountData._rows = [];
    tradeCountData._rows.push({ strategy: 'NEW', SENSEX: '-', BANKNIFTY: '-', NIFTY: '-' });
    renderTradeCountTable();
}

function removeTradeCountRow(btn) {
    const row = btn.closest('tr');
    const idx = parseInt(row.dataset.rowIdx);
    
    if (!isNaN(idx)) {
        tradeCountData._rows.splice(idx, 1);
    }
    renderTradeCountTable();
}

function updateTradeCount(e) {
    const row = e.target.closest('tr');
    const idx = parseInt(row.dataset.rowIdx);
    
    if (!isNaN(idx)) {
        tradeCountData._rows[idx].strategy = row.querySelector('.strategy-input').value;
        tradeCountData._rows[idx].SENSEX = row.querySelector('.sensex-input').value;
        tradeCountData._rows[idx].BANKNIFTY = row.querySelector('.banknifty-input').value;
        tradeCountData._rows[idx].NIFTY = row.querySelector('.nifty-input').value;
        calculateExpectancy();
    }
}

async function calculateExpectancy() {
    const response = await fetch('/calculate_expectancy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            margin_data: convertMarginDataForSave(),
            trade_count: convertTradeCountDataForSave()
        })
    });
    
    expectancyData = await response.json();
    strategyExpectancy = { ...expectancyData };
    renderExpectancyTable();
}

function renderExpectancyTable() {
    const tbody = document.querySelector('#expectancyTable tbody');
    tbody.innerHTML = '';
    
    if (!expectancyData._rows) {
        expectancyData._rows = [];
        Object.keys(expectancyData).forEach(index => {
            if (index === '_rows') return;
            Object.keys(expectancyData[index] || {}).forEach(strategy => {
                const values = expectancyData[index][strategy];
                expectancyData._rows.push({
                    index: index,
                    strategy: strategy,
                    Non_Expiry_WOH: values?.Non_Expiry_WOH || 0,
                    Non_Expiry_WH: values?.Non_Expiry_WH || 0,
                    Expiry_WOH: values?.Expiry_WOH || 0,
                    Expiry_WH: values?.Expiry_WH || 0
                });
            });
        });
    }
    
    expectancyData._rows.forEach((rowData, idx) => {
        const row = document.createElement('tr');
        row.dataset.rowIdx = idx;
        row.innerHTML = `
            <td><input type="text" value="${rowData.index || ''}" class="exp-index-input" data-row-idx="${idx}"></td>
            <td><input type="text" value="${rowData.strategy || ''}" class="exp-strategy-input" data-row-idx="${idx}"></td>
            <td><input type="number" value="${rowData.Non_Expiry_WOH || 0}" class="nexp-woh" data-row-idx="${idx}"></td>
            <td><input type="number" value="${rowData.Non_Expiry_WH || 0}" class="nexp-wh" data-row-idx="${idx}"></td>
            <td><input type="number" value="${rowData.Expiry_WOH || 0}" class="exp-woh" data-row-idx="${idx}"></td>
            <td><input type="number" value="${rowData.Expiry_WH || 0}" class="exp-wh" data-row-idx="${idx}"></td>
            <td><button class="btn btn-sm btn-danger py-0" onclick="removeExpectancyRow(this)">×</button></td>
        `;
        tbody.appendChild(row);
    });
    
    document.querySelectorAll('#expectancyTable input').forEach(el => {
        el.addEventListener('change', updateExpectancyData);
    });
}

function addExpectancyRow() {
    if (!expectancyData._rows) expectancyData._rows = [];
    expectancyData._rows.push({ index: 'INDEX', strategy: 'NEW', Non_Expiry_WOH: 0, Non_Expiry_WH: 0, Expiry_WOH: 0, Expiry_WH: 0 });
    renderExpectancyTable();
}

function removeExpectancyRow(btn) {
    const row = btn.closest('tr');
    const idx = parseInt(row.dataset.rowIdx);
    
    if (!isNaN(idx)) {
        expectancyData._rows.splice(idx, 1);
    }
    renderExpectancyTable();
}

function updateExpectancyData(e) {
    const row = e.target.closest('tr');
    const idx = parseInt(row.dataset.rowIdx);
    
    if (!isNaN(idx)) {
        expectancyData._rows[idx].index = row.querySelector('.exp-index-input').value;
        expectancyData._rows[idx].strategy = row.querySelector('.exp-strategy-input').value;
        expectancyData._rows[idx].Non_Expiry_WOH = parseInt(row.querySelector('.nexp-woh').value) || 0;
        expectancyData._rows[idx].Non_Expiry_WH = parseInt(row.querySelector('.nexp-wh').value) || 0;
        expectancyData._rows[idx].Expiry_WOH = parseInt(row.querySelector('.exp-woh').value) || 0;
        expectancyData._rows[idx].Expiry_WH = parseInt(row.querySelector('.exp-wh').value) || 0;
    }
    strategyExpectancy = { ...expectancyData };
}

function renderClientMarginTable() {
    const tbody = document.querySelector('#clientMarginTable tbody');
    tbody.innerHTML = '';
    
    if (!clientMarginData._rows) {
        clientMarginData._rows = clientMarginData.map(c => ({...c}));
    }
    
    clientMarginData._rows.forEach((client, idx) => {
        const row = document.createElement('tr');
        row.dataset.rowIdx = idx;
        row.innerHTML = `
            <td><input type="text" value="${client.Code || ''}" class="code-input" data-row-idx="${idx}"></td>
            <td><input type="text" value="${client.ClientID || ''}" class="clientid-input" data-row-idx="${idx}"></td>
            <td><input type="number" value="${client.TotalMargin || 0}" class="margin-input" data-row-idx="${idx}"></td>
            <td><button class="btn btn-sm btn-danger py-0" onclick="removeClientRow(this)">×</button></td>
        `;
        tbody.appendChild(row);
    });
    
    clientMarginList = [...clientMarginData._rows];
    
    document.querySelectorAll('#clientMarginTable input').forEach(el => {
        el.addEventListener('change', updateClientMarginData);
    });
}

function addClientRow() {
    if (!clientMarginData._rows) clientMarginData._rows = [...clientMarginData];
    clientMarginData._rows.push({ Code: 'NEW', ClientID: 'CLIENT', TotalMargin: 0 });
    renderClientMarginTable();
}

function removeClientRow(btn) {
    const row = btn.closest('tr');
    const idx = parseInt(row.dataset.rowIdx);
    
    if (!isNaN(idx)) {
        clientMarginData._rows.splice(idx, 1);
    }
    clientMarginList = [...clientMarginData._rows];
    renderClientMarginTable();
}

function updateClientMarginData(e) {
    const row = e.target.closest('tr');
    const idx = parseInt(row.dataset.rowIdx);
    
    if (!isNaN(idx)) {
        clientMarginData._rows[idx].Code = row.querySelector('.code-input').value;
        clientMarginData._rows[idx].ClientID = row.querySelector('.clientid-input').value;
        clientMarginData._rows[idx].TotalMargin = parseInt(row.querySelector('.margin-input').value) || 0;
        clientMarginList = [...clientMarginData._rows];
    }
}

function convertMarginDataForSave() {
    const converted = {};
    if (marginData._rows) {
        marginData._rows.forEach(row => {
            const idx = row.index || 'NIFTY';
            let dayType = row.dayType || 'Non_Expiry';
            if (dayType === 'N.Expiry') dayType = 'Non_Expiry';
            
            if (!converted[idx]) converted[idx] = {};
            converted[idx][dayType] = {
                With_Hedge: row.With_Hedge || 0,
                Without_Hedge: row.Without_Hedge || 0
            };
        });
    }
    return converted;
}

function convertTradeCountDataForSave() {
    const converted = { SENSEX: {}, BANKNIFTY: {}, NIFTY: {} };
    if (tradeCountData._rows) {
        tradeCountData._rows.forEach(row => {
            const strat = row.strategy || 'NEW';
            converted.SENSEX[strat] = row.SENSEX || '-';
            converted.BANKNIFTY[strat] = row.BANKNIFTY || '-';
            converted.NIFTY[strat] = row.NIFTY || '-';
        });
    }
    return converted;
}

function convertExpectancyDataForSave() {
    const converted = {};
    if (expectancyData._rows) {
        expectancyData._rows.forEach(row => {
            const idx = row.index || 'NIFTY';
            const strat = row.strategy || 'NEW';
            if (!converted[idx]) converted[idx] = {};
            converted[idx][strat] = {
                Non_Expiry_WOH: row.Non_Expiry_WOH || 0,
                Non_Expiry_WH: row.Non_Expiry_WH || 0,
                Expiry_WOH: row.Expiry_WOH || 0,
                Expiry_WH: row.Expiry_WH || 0
            };
        });
    }
    return converted;
}

async function saveData() {
    await fetch('/save_data', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            INDEX_MARGIN_DATA: convertMarginDataForSave(),
            STRATEGY_TRADE_COUNT: convertTradeCountDataForSave(),
            STRATEGY_EXPECTANCY: convertExpectancyDataForSave(),
            CLIENT_MARGIN_DATA: clientMarginData._rows || clientMarginData
        })
    });
    alert('Data saved successfully!');
}

loadData();

document.querySelectorAll('#pageTabs button').forEach(tabBtn => {
    tabBtn.addEventListener('shown.bs.tab', function(e) {
        const target = e.target.getAttribute('data-bs-target');
        if (target === '#lot-page' || target === '#margin-page') {
            renderDateDropdown();
        }
    });
});

document.getElementById('marginMultiplier').addEventListener('change', function() {
    marginMultiplier = parseInt(this.value) || 0;
    renderAllocationRows();
});

document.getElementById('marginMultiplier').addEventListener('input', function() {
    marginMultiplier = parseInt(this.value) || 0;
    renderAllocationRows();
});

async function saveManualLots() {
    let lotsData = {};
    document.querySelectorAll('.lot-input').forEach(input => {
        let clientIdx = input.dataset.client;
        let filterIdx = input.dataset.filter;
        let key = `${clientIdx}-${filterIdx}`;
        let val = parseInt(input.value);
        if (!isNaN(val)) {
            lotsData[key] = val;
        }
    });
    
    try {
        const response = await fetch('/save_manual_lots', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                date: selectedDate,
                lotsData: lotsData,
                marginMultiplier: marginMultiplier
            })
        });
        const result = await response.json();
        if (result.status === 'success') {
            alert('Manual lots saved successfully!');
        }
    } catch (e) {
        console.error(e);
        alert('Error saving manual lots');
    }
}

async function generateCSV() {
    let allLotsData = {};
    document.querySelectorAll('.lot-input').forEach(input => {
        let clientIdx = input.dataset.client;
        let filterIdx = input.dataset.filter;
        let key = `${clientIdx}-${filterIdx}`;
        let val = parseInt(input.value);
        if (!isNaN(val)) {
            allLotsData[key] = val;
        }
    });
    
    let clientStrategyLots = [];
    
    clientMarginList.forEach((client, clientIdx) => {
        const clientID = client.ClientID || '';
        
        marginFilters.forEach((mf, filterIdx) => {
            const key = `${clientIdx}-${filterIdx}`;
            let lotVal = allLotsData[key];
            if (lotVal === undefined || lotVal === null || isNaN(lotVal)) {
                lotVal = 1;
            }
            
            clientStrategyLots.push({
                clientId: clientID,
                strategy: mf.strategy,
                indexName: mf.index,
                excelStrategy: mf.excelStrategy || '',
                lot: lotVal
            });
        });
    });
    
    // Apply any temporary changes before generating CSV
    Object.keys(temporaryStrategyChanges).forEach(idx => {
        const rowIdx = parseInt(idx);
        if (strategyDetailsData[rowIdx]) {
            Object.keys(temporaryStrategyChanges[idx]).forEach(field => {
                strategyDetailsData[rowIdx][field] = temporaryStrategyChanges[idx][field];
            });
        }
    });
    
    try {
        const response = await fetch('/generate_csv', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                date: selectedDate,
                lotsData: allLotsData,
                marginMultiplier: marginMultiplier,
                clientMarginData: clientMarginList,
                clientStrategyLots: clientStrategyLots,
                marginData: marginData,
                strategyDetails: strategyDetailsData
            })
        });
        
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            const result = await response.json();
            alert('Error: ' + result.message);
            return;
        }
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `ClientWiseTradeFiles_${selectedDate}.zip`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        } else {
            alert('Error generating CSV files');
        }
    } catch (e) {
        console.error(e);
        alert('Error generating CSV files');
    }
}

function renderDateDropdown() {
    const select = document.getElementById('dateSelect');
    select.innerHTML = '<option value="">Select Date</option>';
    allDates.forEach(date => {
        const option = document.createElement('option');
        option.value = date;
        option.textContent = date;
        select.appendChild(option);
    });
    select.addEventListener('change', async (e) => {
        selectedDate = e.target.value;
        if (selectedDate) {
            const response = await fetch('/get_lot_data?date=' + encodeURIComponent(selectedDate));
            const data = await response.json();
            renderLotTable(data);
            
            const stratResponse = await fetch('/get_strategies_for_date?date=' + encodeURIComponent(selectedDate));
            const stratData = await stratResponse.json();
            availableStrategiesFromFile = stratData.strategies || [];
            
            const allocResponse = await fetch('/get_allocation_data?date=' + encodeURIComponent(selectedDate));
            const allocData = await allocResponse.json();
            
            const nf = data.NF || {};
            const snx = data.SNX || {};
            
            let effectiveEntryDay = allocData.entryDay;
            
            if (nf.EntryDay === 'Monday' && nf.DTE === 0) {
                effectiveEntryDay = 'Tuesday';
            } else if (snx.EntryDay === 'Wednesday' && snx.DTE === 0) {
                effectiveEntryDay = 'Thursday';
            }
            
            allocData.effectiveEntryDay = effectiveEntryDay;
            
            savedMarginMultiplier = allocData.savedMarginMultiplier || 15;
            marginMultiplier = savedMarginMultiplier;
            document.getElementById('marginMultiplier').value = marginMultiplier;
            manualLots = {};
            
            const allocationCard = document.getElementById('allocationCard');
            if (effectiveEntryDay) {
                allocationCard.style.display = 'block';
                renderAllocationTable(allocData);
            } else {
                allocationCard.style.display = 'none';
            }
            
            // Load strategy details for the selected date
            await loadStrategyDetails();
        } else {
            // Hide strategy details when no date selected
            document.getElementById('strategyDetailsCard').style.display = 'none';
            strategyDetailsData = [];
            temporaryStrategyChanges = {};
            renderStrategyDetailsTable();
        }
    });
}

function renderLotTable(data) {
    const tbody = document.querySelector('#lotTable tbody');
    tbody.innerHTML = '';
    
    const nf = data.NF || {};
    const bnf = data.BNF || {};
    const snx = data.SNX || {};
    const entryDay = nf.EntryDay || bnf.EntryDay || snx.EntryDay || '-';
    
    const tr = document.createElement('tr');
    tr.innerHTML = `
        <td>${selectedDate}</td>
        <td>${entryDay}</td>
        <td>${nf.ExpiryDate || '-'}</td>
        <td>${nf.DTE !== undefined && nf.DTE !== null ? nf.DTE : '-'}</td>
        <td>${bnf.ExpiryDate || '-'}</td>
        <td>${bnf.WTE !== undefined && bnf.WTE !== null ? bnf.WTE : '-'}</td>
        <td>${snx.ExpiryDate || '-'}</td>
        <td>${snx.DTE !== undefined && snx.DTE !== null ? snx.DTE : '-'}</td>
    `;
    tbody.appendChild(tr);
}

let marginFilters = [];
let availableStrategiesFromFile = [];
let strategyDetailsData = []; // To hold the strategy details for the selected date
let temporaryStrategyChanges = {}; // To hold temporary changes to strategy details

let columnConfigs = {
    'DYNAMIC SL': [
        { type: 'N.Expiry', index: 'SENSEX', wh: 'W.H', percent: 10 },
        { type: 'N.Expiry', index: 'BANKNIFTY', wh: 'W.O.H', percent: 10 },
        { type: 'N.Expiry', index: 'NIFTY', wh: 'W.H', percent: 10 }
    ],
    'ITM SH': [
        { type: 'N.Expiry', index: 'NIFTY', wh: 'W.H', percent: 0 },
        { type: 'Expiry', index: 'NIFTY', wh: 'W.H', percent: 0 }
    ],
    'TO': [
        { type: 'N.Expiry', index: 'NIFTY', wh: 'W.H', percent: 0 }
    ],
    'NFBT RB': [],
    'NFBT TR': [],
    'NFBT BTF': []
};

let expectancyHeaders = {
    'N.Expiry': { 'W.H': 'Non_Expiry_WH', 'W.O.H': 'Non_Expiry_WOH' },
    'Expiry': { 'W.H': 'Expiry_WH', 'W.O.H': 'Expiry_WOH' }
};

function getAvailableOptions() {
    const options = { type: [], indices: [], wh: [] };
    const indices = ['SENSEX', 'BANKNIFTY', 'NIFTY'];
    const types = ['N.Expiry', 'Expiry'];
    const whOptions = ['W.H', 'W.O.H'];
    
    indices.forEach(idx => {
        if (strategyExpectancy[idx]) {
            Object.keys(strategyExpectancy[idx]).forEach(strat => {
                const stratData = strategyExpectancy[idx][strat];
                if (stratData.Non_Expiry_WH || stratData.Non_Expiry_WOH) {
                    if (!options.type.includes('N.Expiry')) options.type.push('N.Expiry');
                }
                if (stratData.Expiry_WH || stratData.Expiry_WOH) {
                    if (!options.type.includes('Expiry')) options.type.push('Expiry');
                }
            });
        }
    });
    
    options.indices = indices;
    options.wh = whOptions;
    
    return options;
}

function getEntryDayConfig(entryDay) {
    const strategyTypeMap = {
        'DYNAMIC SL': 'N.Expiry',
        'INDEXMOVE': 'N.Expiry',
        'TO': 'Expiry',
        '2T3 TO': 'Expiry',
        'SENSEX TO': 'Expiry',
        'NIFTY TO': 'Expiry',
        'ITM SH': 'Expiry'
    };
    
    if (availableStrategiesFromFile.length > 0) {
        const config = {};
        availableStrategiesFromFile.forEach(s => {
            const stratName = s.strategy;
            
            // INDEXMOVE only for NIFTY
            if (stratName === 'INDEXMOVE' && s.index !== 'NIFTY') return;
            
            if (!config[stratName]) config[stratName] = [];
            const type = strategyTypeMap[stratName] || 'N.Expiry';
            
            // Get percent from day-based config
            const dayConfig = getDayBasedConfig(entryDay);
            const stratConfig = dayConfig[stratName] || [];
            const percentConfig = stratConfig.find(c => c.index === s.index);
            const percent = percentConfig ? percentConfig.percent : 10;
            
            // For DYNAMIC SL, use W.O.H for BANKNIFTY, W.H for others
            // For INDEXMOVE, use W.O.H by default
            let wh = 'W.H';
            if (stratName === 'DYNAMIC SL' && s.index === 'BANKNIFTY') {
                wh = 'W.O.H';
            } else if (stratName === 'INDEXMOVE') {
                wh = 'W.O.H';
            }
            
            config[stratName].push({
                type: type,
                index: s.index,
                wh: wh,
                percent: percent
            });
        });
        return config;
    }
    
    return getDayBasedConfig(entryDay);
}

function getDayBasedConfig(entryDay) {
    if (entryDay === 'Monday' || entryDay === 'Wednesday' || entryDay === 'Friday') {
        return {
            'INDEXMOVE': [
                { type: 'N.Expiry', index: 'NIFTY', wh: 'W.O.H', percent: 15 }
            ],
            'DYNAMIC SL': [
                { type: 'N.Expiry', index: 'SENSEX', wh: 'W.H', percent: 10 },
                { type: 'N.Expiry', index: 'BANKNIFTY', wh: 'W.O.H', percent: 5 },
                { type: 'N.Expiry', index: 'NIFTY', wh: 'W.H', percent: 10 }
            ]
        };
    } else if (entryDay === 'Tuesday') {
        return {
            'INDEXMOVE': [
                { type: 'N.Expiry', index: 'NIFTY', wh: 'W.O.H', percent: 15 }
            ],
            'DYNAMIC SL': [
                { type: 'N.Expiry', index: 'SENSEX', wh: 'W.H', percent: 10 },
                { type: 'N.Expiry', index: 'BANKNIFTY', wh: 'W.O.H', percent: 5 },
                { type: 'N.Expiry', index: 'NIFTY', wh: 'W.H', percent: 10 }
            ],
            'ITM SH': [
                { type: 'Expiry', index: 'NIFTY', wh: 'W.H', percent: 10, excelStrategy: 'I_2T23' }
            ],
            'TO': [
                { type: 'Expiry', index: 'NIFTY', wh: 'W.H', percent: 45 }
            ]
        };
    } else if (entryDay === 'Thursday') {
        return {
            'INDEXMOVE': [
                { type: 'N.Expiry', index: 'NIFTY', wh: 'W.O.H', percent: 15 }
            ],
            'DYNAMIC SL': [
                { type: 'N.Expiry', index: 'SENSEX', wh: 'W.H', percent: 10 },
                { type: 'N.Expiry', index: 'BANKNIFTY', wh: 'W.O.H', percent: 5 },
                { type: 'N.Expiry', index: 'NIFTY', wh: 'W.H', percent: 10 }
            ],
            '2T3 TO': [
                { type: 'Expiry', index: 'SENSEX', wh: 'W.H', percent: 10, excelStrategy: 'SV4' }
            ],
            'TO': [
                { type: 'Expiry', index: 'SENSEX', wh: 'W.H', percent: 40 }
            ]
        };
    }
    return {};
}

function renderAllocationTable(data) {
    const thead = document.querySelector('#allocationTable thead');
    const tbody = document.querySelector('#allocationTable tbody');
    thead.innerHTML = '';
    tbody.innerHTML = '';
    
    if (!data.effectiveEntryDay || !data.clients || data.clients.length === 0) {
        return;
    }
    
    const availableOptions = getAvailableOptions();
    const entryConfig = getEntryDayConfig(data.effectiveEntryDay);
    marginFilters = [];
    
    Object.keys(entryConfig).forEach(strategy => {
        if (entryConfig[strategy] && entryConfig[strategy].length > 0) {
            entryConfig[strategy].forEach(config => {
                marginFilters.push({ strategy: strategy, ...config });
            });
        }
    });
    
    const rowCount = 5;
    const theadRows = [];
    for (let i = 0; i < rowCount; i++) theadRows.push(document.createElement('tr'));
    
    for (let i = 0; i < 3; i++) {
        const thCode = document.createElement('th');
        thCode.textContent = i === 0 ? 'Code' : '';
        theadRows[i].appendChild(thCode);
        
        const thClient = document.createElement('th');
        thClient.textContent = i === 0 ? 'ClientID' : '';
        theadRows[i].appendChild(thClient);
        
        const thPercent = document.createElement('th');
        thPercent.textContent = i === 0 ? '%' : '';
        thPercent.style.width = '70px';
        theadRows[i].appendChild(thPercent);
        
        const thMargin = document.createElement('th');
        thMargin.textContent = i === 0 ? 'Total Margin' : '';
        theadRows[i].appendChild(thMargin);
    }
    
    for (let i = 3; i < rowCount; i++) {
        theadRows[i].innerHTML = '<th></th><th></th><th></th><th></th>';
    }
    
    marginFilters.forEach((mf, idx) => {
        const selectType = document.createElement('select');
        selectType.setAttribute('data-idx', idx);
        selectType.setAttribute('data-field', 'type');
        selectType.style.cssText = 'border:1px solid #000;padding:3px;font-size:13px;width:80px;background:#fff;cursor:pointer;border-radius:4px;white-space:nowrap;';
        
        let typeOptionsHtml = '';
        availableOptions.type.forEach(t => {
            typeOptionsHtml += `<option value="${t}" ${t === mf.type ? 'selected' : ''}>${t}</option>`;
        });
        selectType.innerHTML = typeOptionsHtml || '<option value="N.Expiry">N.Expiry</option><option value="Expiry">Expiry</option>';
        selectType.onchange = function() { updateMarginFilter(idx, 'type', this.value); };
        
        const th1 = document.createElement('th');
        th1.style.padding = '1px';
        th1.style.fontSize = '12px';
        th1.style.fontWeight = 'bold';
        th1.style.whiteSpace = 'nowrap';
        th1.textContent = mf.index;
        
        const th2 = document.createElement('th');
        th2.style.padding = '1px';
        th2.style.fontSize = '12px';
        th2.style.fontWeight = 'bold';
        th2.textContent = mf.excelStrategy || mf.strategy;
        
        const th3 = document.createElement('th');
        th3.style.padding = '1px';
        th3.vAlign = 'bottom';
        th3.appendChild(selectType);
        
        const selectWh = document.createElement('select');
        selectWh.setAttribute('data-idx', idx);
        selectWh.setAttribute('data-field', 'wh');
        selectWh.style.cssText = 'border:1px solid #000;padding:3px;font-size:13px;width:80px;background:#fff;cursor:pointer;border-radius:4px;white-space:nowrap;';
        
        let whOptionsHtml = '';
        availableOptions.wh.forEach(w => {
            whOptionsHtml += `<option value="${w}" ${w === mf.wh ? 'selected' : ''}>${w}</option>`;
        });
        selectWh.innerHTML = whOptionsHtml || '<option value="W.H">W.H</option><option value="W.O.H">W.O.H</option>';
        selectWh.onchange = function() { updateMarginFilter(idx, 'wh', this.value); };
        
        const th4 = document.createElement('th');
        th4.style.padding = '1px';
        th4.vAlign = 'top';
        th4.appendChild(selectWh);
        
        const th5 = document.createElement('th');
        th5.style.padding = '1px';
        const percentWrapper = document.createElement('span');
        percentWrapper.style.whiteSpace = 'nowrap';
        const percentInput = document.createElement('input');
        percentInput.type = 'number';
        percentInput.value = mf.percent || 0;
        percentInput.setAttribute('data-idx', idx);
        percentInput.setAttribute('data-field', 'percent');
        percentInput.style.cssText = 'width:40px;padding:2px;font-size:11px;text-align:center;border:1px solid #000;';
        percentInput.onchange = function() { updateMarginFilter(idx, 'percent', parseInt(this.value) || 0); };
        const percentSign = document.createElement('span');
        percentSign.textContent = '%';
        percentSign.style.fontSize = '12px';
        percentWrapper.appendChild(percentInput);
        percentWrapper.appendChild(percentSign);
        th5.appendChild(percentWrapper);
        
        theadRows[0].appendChild(th1);
        theadRows[1].appendChild(th2);
        theadRows[2].appendChild(th3);
        theadRows[3].appendChild(th4);
        theadRows[4].appendChild(th5);
        
        if (showMarginUsed) {
            const thUsed = document.createElement('th');
            thUsed.textContent = '%';
            thUsed.style.background = '#f5f5f5';
            thUsed.style.fontSize = '10px';
            theadRows[1].appendChild(thUsed);
        }
    });
    
    if (showMarginUsed) {
        const thTotalUsed = document.createElement('th');
        thTotalUsed.textContent = 'Total';
        thTotalUsed.style.background = '#e0e0e0';
        thTotalUsed.style.fontWeight = 'bold';
        thTotalUsed.style.fontSize = '10px';
        
        theadRows[1].appendChild(thTotalUsed);
        
        const thTotalUsedPct = document.createElement('th');
        thTotalUsedPct.textContent = 'Total Used %';
        thTotalUsedPct.style.background = '#d0d0d0';
        thTotalUsedPct.style.fontWeight = 'bold';
        thTotalUsedPct.style.fontSize = '10px';
        
        theadRows[1].appendChild(thTotalUsedPct);
        
        for (let i = 2; i < rowCount; i++) {
            theadRows[i].innerHTML = '<th></th><th></th>';
        }
    }
    
    theadRows.forEach(row => thead.appendChild(row));
    renderAllocationRows();
}

function updateMarginFilter(idx, field, value) {
    marginFilters[idx][field] = value;
    renderAllocationRows();
}

function formatMargin(value) {
    if (value >= 10000000) {
        return (value / 10000000).toFixed(2) + ' Cr';
    } else if (value >= 100000) {
        return (value / 100000).toFixed(0) + ' L';
    }
    return value.toString();
}

let clientPercentages = {};
let marginMultiplier = 15;
let manualLots = {};
let savedMarginMultiplier = 15;

function getExpectancyValue(index, strategy) {
    // Try direct match first
    if (strategyExpectancy[index] && strategyExpectancy[index][strategy]) {
        return strategyExpectancy[index][strategy];
    }
    // Try partial match for strategies like TO, 2T3 TO
    if (strategyExpectancy[index]) {
        const keys = Object.keys(strategyExpectancy[index]);
        const matched = keys.find(k => k.includes(strategy) || strategy.includes(k));
        if (matched) return strategyExpectancy[index][matched];
    }
    if (strategyExpectancy._rows) {
        const row = strategyExpectancy._rows.find(r => r.index === index && r.strategy === strategy);
        if (row) return row;
    }
    return null;
}

let showMarginUsed = false;

function toggleMarginUsed() {
    showMarginUsed = !showMarginUsed;
    renderAllocationRows();
}

function renderAllocationRows() {
    const tbody = document.querySelector('#allocationTable tbody');
    tbody.innerHTML = '';
    
    clientMarginList.forEach((client, idx) => {
        const currentPercent = clientPercentages[idx] || 100;
        const percentFactor = currentPercent / 100;
        
        const tr1 = document.createElement('tr');
        tr1.innerHTML = `
            <td>${client.Code}</td>
            <td>${client.ClientID}</td>
            <td><select data-client-idx="${idx}" style="border:1px solid #000;padding:2px;font-size:11px;width:55px;background:#fff;cursor:pointer;border-radius:3px;">
                <option value="100" ${currentPercent === 100 ? 'selected' : ''}>100%</option>
                <option value="75" ${currentPercent === 75 ? 'selected' : ''}>75%</option>
                <option value="50" ${currentPercent === 50 ? 'selected' : ''}>50%</option>
                <option value="25" ${currentPercent === 25 ? 'selected' : ''}>25%</option>
            </select></td>
            <td>${formatMargin(client.TotalMargin)}</td>`;
        
        marginFilters.forEach((mf, filterIdx) => {
            const expKey = mf.type === 'N.Expiry' ? 'Non_Expiry' : 'Expiry';
            const expData = getExpectancyValue(mf.index, mf.strategy);
            let marginValue = 0;
            if (expData) {
                if (mf.wh === 'W.H') marginValue = expData[expKey + '_WH'] || 0;
                else if (mf.wh === 'W.O.H') marginValue = expData[expKey + '_WOH'] || 0;
            }
            
            let percentValue = mf.percent || 0;
            let totalMargin = client.TotalMargin || 0;
            let key = `${idx}-${filterIdx}`;
            
            let displayValue = '-';
            let lotVal = 0;
            
            if (marginValue > 0) {
                let fullLots100 = Math.floor(((totalMargin * percentValue) / 100) / marginValue);
                let marginWithExtra = totalMargin * (1 + marginMultiplier / 100);
                let lotsWithExtra100 = Math.floor(((marginWithExtra * percentValue) / 100) / marginValue);
                let baseLots100 = fullLots100;
                if (lotsWithExtra100 > fullLots100) baseLots100 = fullLots100 + 1;
                if (baseLots100 < 1) baseLots100 = 1;
                
                let finalLots = Math.floor(baseLots100 * percentFactor);
                
                if (currentPercent === 50 && baseLots100 > 1 && baseLots100 % 2 !== 0) {
                    finalLots = Math.floor(baseLots100 / 2) + 1;
                } else if (currentPercent === 75) {
                    if (baseLots100 % 4 !== 0 && baseLots100 > 3) {
                        finalLots = Math.floor(baseLots100 * 3 / 4) + 1;
                    } else {
                        finalLots = Math.floor(baseLots100 * 3 / 4);
                    }
                    if (finalLots < 1) finalLots = 1;
                } else if (currentPercent === 25) {
                    if (baseLots100 > 1 && baseLots100 % 2 !== 0) {
                        finalLots = Math.floor(baseLots100 / 4) + 1;
                    } else {
                        finalLots = Math.floor(baseLots100 / 4);
                    }
                    if (finalLots < 1) finalLots = 1;
                }
                
                if (finalLots < 1) finalLots = 1;
                displayValue = finalLots;
                lotVal = finalLots;
            }
            
            let isManual = manualLots[key] !== undefined;
            let isManualZero = isManual && manualLots[key] === 0;
            let val = isManual ? manualLots[key] : displayValue;
            
            tr1.innerHTML += `<td>
                <input type="number" class="lot-input" data-client="${idx}" data-filter="${filterIdx}" 
                value="${val}" ${isManualZero ? '' : 'min="1"'} style="background:${isManual ? '#ffff00' : 'transparent'};width:55px;padding:2px;font-size:11px;border:1px solid #ccc;text-align:center;">
            </td>`;
        });
        
        tbody.appendChild(tr1);
        
        if (showMarginUsed) {
            const tr2 = document.createElement('tr');
            let html2 = `<td colspan="4"></td>`;
            let totalMarginUsedPercent = 0;
            
            marginFilters.forEach((mf, filterIdx) => {
                const expKey = mf.type === 'N.Expiry' ? 'Non_Expiry' : 'Expiry';
                const expData = getExpectancyValue(mf.index, mf.strategy);
                let marginValue = 0;
                if (expData) {
                    if (mf.wh === 'W.H') marginValue = expData[expKey + '_WH'] || 0;
                    else if (mf.wh === 'W.O.H') marginValue = expData[expKey + '_WOH'] || 0;
                }
                
                let totalMargin = client.TotalMargin || 0;
                let key = `${idx}-${filterIdx}`;
                let lotVal = manualLots[key] !== undefined ? manualLots[key] : parseInt(tr1.querySelector(`input[data-filter="${filterIdx}"]`).value) || 0;
                
                if (lotVal > 0 && marginValue > 0 && totalMargin > 0) {
                    let marginUsedPercent = (marginValue * lotVal) / totalMargin * 100;
                    totalMarginUsedPercent += marginUsedPercent;
                    let assignedPercent = mf.percent || 0;
                    let bgColor = marginUsedPercent > assignedPercent ? '#add8e6' : '#f0f0f0';
                    let textColor = marginUsedPercent > assignedPercent ? '#000' : '#666';
                    html2 += `<td style="font-size:9px;color:${textColor};text-align:center;background:${bgColor};padding:2px;">${marginUsedPercent.toFixed(2)}%</td>`;
                } else {
                    html2 += `<td style="font-size:9px;color:#999;text-align:center;background:#f0f0f0;padding:2px;">-</td>`;
                }
            });
            
            html2 += `<td style="font-size:10px;font-weight:bold;color:#000;text-align:center;background:#e0e0e0;padding:2px;">${totalMarginUsedPercent.toFixed(2)}%</td>`;
            
            tr2.innerHTML = html2;
            tbody.appendChild(tr2);
        }
        
        const newSelect = tr1.querySelector('select[data-client-idx]');
        if (newSelect) {
            newSelect.onchange = function() {
                clientPercentages[idx] = parseInt(this.value);
                renderAllocationRows();
            };
        }
    });
    
    document.querySelectorAll('.lot-input').forEach(input => {
        input.addEventListener('change', function() {
            const clientIdx = this.dataset.client;
            const filterIdx = this.dataset.filter;
            let key = `${clientIdx}-${filterIdx}`;
            let val = parseInt(this.value);
            if (!isNaN(val) && val >= 0) {
                manualLots[key] = val;
                this.style.background = '#ffff00';
            } else {
                delete manualLots[key];
                this.style.background = 'transparent';
            }
            if (showMarginUsed) {
                renderAllocationRows();
            }
        });
    });
}

async function refreshLots() {
    if (!selectedDate) return;
    
    manualLots = {};
    clientPercentages = {};
    document.getElementById('marginMultiplier').value = 15;
    
    const response = await fetch('/get_lot_data?date=' + encodeURIComponent(selectedDate));
    const data = await response.json();
    
    const stratResponse = await fetch('/get_strategies_for_date?date=' + encodeURIComponent(selectedDate));
    const stratData = await stratResponse.json();
    availableStrategiesFromFile = stratData.strategies || [];
    
    const allocResponse = await fetch('/get_allocation_data?date=' + encodeURIComponent(selectedDate));
    const allocData = await allocResponse.json();
    
    const nf = data.NF || {};
    const snx = data.SNX || {};
    
    let effectiveEntryDay = allocData.entryDay;
    
    if (nf.EntryDay === 'Monday' && nf.DTE === 0) {
        effectiveEntryDay = 'Tuesday';
    } else if (snx.EntryDay === 'Wednesday' && snx.DTE === 0) {
        effectiveEntryDay = 'Thursday';
    }
    
allocData.effectiveEntryDay = effectiveEntryDay;
            
            const allocationCard = document.getElementById('allocationCard');
            if (allocData && allocData.clients && allocData.clients.length > 0) {
                allocationCard.style.display = 'block';
                renderAllocationTable(allocData);
            } else {
                allocationCard.style.display = 'none';
            }
    
    // Also load strategy details when refreshing
    await loadStrategyDetails();
}

function updateFileName() {
    const fileInput = document.getElementById('strategyFileInput');
    const fileNameDisplay = document.getElementById('fileNameDisplay');
    const statusDiv = document.getElementById('uploadStatus');
    
    if (fileInput.files && fileInput.files.length > 0) {
        fileNameDisplay.value = fileInput.files[0].name;
    } else {
        fileNameDisplay.value = 'Please select file';
    }
    statusDiv.innerHTML = '';
}

document.addEventListener('DOMContentLoaded', function() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('strategyFileInput');
    const fileNameDisplay = document.getElementById('fileNameDisplay');
    
    dropZone.addEventListener('click', () => fileInput.click());
    
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('border-success', 'bg-light');
    });
    
    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('border-success', 'bg-light');
    });
    
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('border-success', 'bg-light');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            fileNameDisplay.value = files[0].name;
            document.getElementById('uploadStatus').innerHTML = '';
        }
    });
});

async function uploadStrategyFile() {
    const fileInput = document.getElementById('strategyFileInput');
    const fileNameDisplay = document.getElementById('fileNameDisplay');
    const statusDiv = document.getElementById('uploadStatus');
    
    if (!fileInput.files || fileInput.files.length === 0) {
        statusDiv.innerHTML = '<span class="text-danger">Please select file</span>';
        return;
    }
    
    const file = fileInput.files[0];
    if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
        statusDiv.innerHTML = '<span class="text-danger">Invalid file type. Please upload .xlsx or .xls file</span>';
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/upload_strategy_file', {
            method: 'POST',
            body: formData
        });
        const result = await response.json();
        
        if (result.status === 'success') {
            statusDiv.innerHTML = '<span class="text-success">' + result.message + '</span>';
            fileInput.value = '';
            fileNameDisplay.value = 'Please select file';
        } else {
            statusDiv.innerHTML = '<span class="text-danger">' + result.message + '</span>';
        }
    } catch (e) {
        statusDiv.innerHTML = '<span class="text-danger">Error uploading file</span>';
    }
}

// Strategy Details Functions
async function loadStrategyDetails() {
    if (!selectedDate) return;
    
    try {
        const response = await fetch('/get_strategy_details?date=' + encodeURIComponent(selectedDate));
        const data = await response.json();
        
        console.log('Strategy details response:', data);
        
        strategyDetailsData = data.strategies || [];
        temporaryStrategyChanges = {};
        renderStrategyDetailsTable();
        
        document.getElementById('strategyDetailsCard').style.display = 'block';
    } catch (e) {
        console.error('Error loading strategy details:', e);
        document.getElementById('strategyDetailsCard').style.display = 'none';
    }
}

function renderStrategyDetailsTable() {
    const tbody = document.querySelector('#strategyDetailsTable tbody');
    tbody.innerHTML = '';
    
    strategyDetailsData.forEach((strategy, idx) => {
        let slValue = strategy['SL%'] || '0';
        let slDisplay;
        if (typeof slValue === 'string' && slValue.includes('_')) {
            slDisplay = slValue;
        } else if (typeof slValue === 'string') {
            slDisplay = slValue + '%';
        } else if (typeof slValue === 'number' && slValue > 0 && slValue < 1) {
            slDisplay = Math.round(slValue * 100) + '%';
        } else {
            slDisplay = String(slValue) + '%';
        }
        
        const row = document.createElement('tr');
        row.dataset.rowIdx = idx;
        row.innerHTML = `
            <td style="width:40px;"><button class="btn btn-sm btn-success py-0" onclick="insertStrategyDetailsRow(this)">+</button></td>
            <td><input type="text" value="${strategy['Main Strategy'] || ''}" class="form-control form-control-sm main-strategy-input" data-row-idx="${idx}"></td>
            <td><input type="number" value="${strategy['DTE/WTE'] || 0}" class="form-control form-control-sm dte-wte-input" data-row-idx="${idx}"></td>
            <td><input type="text" value="${strategy['Segment'] || ''}" class="form-control form-control-sm segment-input" data-row-idx="${idx}"></td>
            <td><input type="text" value="${strategy['Strategy'] || ''}" class="form-control form-control-sm strategy-input" data-row-idx="${idx}"></td>
            <td><input type="text" value="${strategy['Exchange'] || ''}" class="form-control form-control-sm exchange-input" data-row-idx="${idx}"></td>
            <td><input type="text" value="${strategy['Symbol'] || ''}" class="form-control form-control-sm symbol-input" data-row-idx="${idx}"></td>
            <td><input type="text" value="${strategy['Entry Time'] || ''}" class="form-control form-control-sm entry-time-input" data-row-idx="${idx}"></td>
            <td><input type="text" value="${strategy['Exit Time'] || ''}" class="form-control form-control-sm exit-time-input" data-row-idx="${idx}"></td>
            <td><input type="text" value="${strategy['Strike'] || 'ATM'}" class="form-control form-control-sm strike-input" data-row-idx="${idx}"></td>
            <td><input type="text" value="${strategy['Option Type'] || 'CE& PE Both'}" class="form-control form-control-sm option-type-input" data-row-idx="${idx}"></td>
            <td><input type="text" value="${strategy['Side'] || 'Sell'}" class="form-control form-control-sm side-input" data-row-idx="${idx}"></td>
            <td style="width:40px;"><input type="text" value="${slDisplay}" class="form-control form-control-sm sl-percentage-input" data-row-idx="${idx}"></td>
            <td><input type="text" value="${strategy['Remarks'] || ''}" class="form-control form-control-sm remarks-input" data-row-idx="${idx}"></td>
            <td style="width:40px;"><button class="btn btn-sm btn-danger py-0" onclick="removeStrategyDetailsRow(this)">×</button></td>
        `;
        row.style.cursor = 'pointer';
        row.addEventListener('click', function(e) {
            if (e.target.tagName === 'BUTTON' || e.target.tagName === 'INPUT') return;
            this.classList.toggle('selected');
        });
        tbody.appendChild(row);
    });
    
    // Add event listeners to all inputs
    document.querySelectorAll('#strategyDetailsTable input').forEach(input => {
        input.addEventListener('change', function() {
            const row = this.closest('tr');
            const idx = parseInt(row.dataset.rowIdx);
            const className = this.className;
            
            let field = '';
            if (className.includes('main-strategy-input')) field = 'Main Strategy';
            else if (className.includes('dte-wte-input')) field = 'DTE/WTE';
            else if (className.includes('segment-input')) field = 'Segment';
            else if (className.includes('strategy-input')) field = 'Strategy';
            else if (className.includes('exchange-input')) field = 'Exchange';
            else if (className.includes('symbol-input')) field = 'Symbol';
            else if (className.includes('entry-time-input')) field = 'Entry Time';
            else if (className.includes('exit-time-input')) field = 'Exit Time';
            else if (className.includes('strike-input')) field = 'Strike';
            else if (className.includes('option-type-input')) field = 'Option Type';
            else if (className.includes('side-input')) field = 'Side';
            else if (className.includes('sl-percentage-input')) {
                field = 'SL%';
                let val = this.value.trim();
                if (val.includes('_')) {
                    this.dataset.decimalValue = val;
                } else {
                    val = val.replace('%', '').trim();
                    this.value = val + '%';
                    this.dataset.decimalValue = val;
                }
            }
            else if (className.includes('remarks-input')) field = 'Remarks';
            
            if (!field || isNaN(idx)) return;
            
            // Store the value
            if (field === 'SL%' && this.dataset.decimalValue !== undefined) {
                strategyDetailsData[idx][field] = parseFloat(this.dataset.decimalValue);
            } else {
                strategyDetailsData[idx][field] = this.value;
            }
            
            // Store the change in temporary changes
            if (!temporaryStrategyChanges[idx]) {
                temporaryStrategyChanges[idx] = {};
            }
            temporaryStrategyChanges[idx][field] = this.value;
        });
    });
}

function addStrategyRow() {
    // Add a new empty row to the strategy details
    strategyDetailsData.push({
        'Main Strategy': '',
        'DTE/WTE': 0,
        'Segment': '',
        'Strategy': '',
        'Exchange': '',
        'Symbol': '',
        'Entry Time': '',
        'Exit Time': '',
        'Strike': 'ATM',
        'Option Type': 'CE& PE Both',
        'Side': 'Sell',
        'SL%': '0',
        'Remarks': ''
    });
    
    renderStrategyDetailsTable();
}

function insertStrategyDetailsRow(btn) {
    const row = btn.closest('tr');
    const idx = parseInt(row.dataset.rowIdx);
    
    const currentStrategy = strategyDetailsData[idx];
    const newStrategy = {
        'Main Strategy': currentStrategy['Main Strategy'] || '',
        'DTE/WTE': currentStrategy['DTE/WTE'] || 0,
        'Segment': currentStrategy['Segment'] || '',
        'Strategy': currentStrategy['Strategy'] || '',
        'Exchange': currentStrategy['Exchange'] || '',
        'Symbol': currentStrategy['Symbol'] || '',
        'Entry Time': currentStrategy['Entry Time'] || '',
        'Exit Time': currentStrategy['Exit Time'] || '',
        'Strike': currentStrategy['Strike'] || 'ATM',
        'Option Type': currentStrategy['Option Type'] || 'CE& PE Both',
        'Side': currentStrategy['Side'] || 'Sell',
        'SL%': currentStrategy['SL%'] || '0',
        'Remarks': currentStrategy['Remarks'] || ''
    };
    
    strategyDetailsData.splice(idx, 0, newStrategy);
    
    renderStrategyDetailsTable();
}

function removeStrategyDetailsRow(btn) {
    const row = btn.closest('tr');
    const idx = parseInt(row.dataset.rowIdx);
    
    if (!isNaN(idx)) {
        strategyDetailsData.splice(idx, 1);
        // Also remove any temporary changes for this row
        delete temporaryStrategyChanges[idx];
        // Re-index the temporary changes object
        const newChanges = {};
        strategyDetailsData.forEach((strategy, newIdx) => {
            if (temporaryStrategyChanges[newIdx + 1]) { // Original index was shifted
                newChanges[newIdx] = temporaryStrategyChanges[newIdx + 1];
            } else if (temporaryStrategyChanges[newIdx]) {
                newChanges[newIdx] = temporaryStrategyChanges[newIdx];
            }
        });
        temporaryStrategyChanges = newChanges;
    }
    
    renderStrategyDetailsTable();
}

function deleteStrategyRow() {
    const selectedRows = document.querySelectorAll('#strategyDetailsTable tbody tr.selected');
    if (selectedRows.length === 0) {
        alert('Please select rows to delete');
        return;
    }
    
    // Get indices in descending order to avoid issues when removing
    const indices = Array.from(selectedRows)
        .map(row => parseInt(row.dataset.rowIdx))
        .sort((a, b) => b - a);
    
    indices.forEach(idx => {
        if (!isNaN(idx) && idx >= 0 && idx < strategyDetailsData.length) {
            strategyDetailsData.splice(idx, 1);
            delete temporaryStrategyChanges[idx];
        }
    });
    
    // Re-index temporary changes
    const newChanges = {};
    strategyDetailsData.forEach((strategy, newIdx) => {
        // Find if there were changes for this original index
        let found = false;
        for (const [origIdx, changes] of Object.entries(temporaryStrategyChanges)) {
            if (parseInt(origIdx) >= newIdx && 
                (parseInt(origIdx) - newIdx) < Object.keys(temporaryStrategyChanges).length) {
                // This is a simplification - in a real app we'd need better mapping
                newChanges[newIdx] = changes || {};
                found = true;
                break;
            }
        }
        if (!found) {
            newChanges[newIdx] = {};
        }
    });
    temporaryStrategyChanges = newChanges;
    
    renderStrategyDetailsTable();
}

function saveTemporaryStrategyChanges() {
    // Temporary changes are already being tracked in temporaryStrategyChanges object
    // We just need to apply them to the main data for display purposes
    Object.keys(temporaryStrategyChanges).forEach(idx => {
        const rowIdx = parseInt(idx);
        if (strategyDetailsData[rowIdx]) {
            Object.keys(temporaryStrategyChanges[idx]).forEach(field => {
                strategyDetailsData[rowIdx][field] = temporaryStrategyChanges[idx][field];
            });
        }
    });
    
    // Clear the temporary changes since they're now applied
    temporaryStrategyChanges = {};
    
    // Re-render to reflect the applied changes
    renderStrategyDetailsTable();
    
    alert('Temporary changes saved and applied to current view');
}

async function savePermanentStrategyChanges() {
    if (!selectedDate) {
        alert('Please select a date first');
        return;
    }
    
    try {
        const response = await fetch('/save_strategy_details', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                date: selectedDate,
                strategies: strategyDetailsData
            })
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            // Clear temporary changes after saving
            temporaryStrategyChanges = {};
            
            // Re-render
            renderStrategyDetailsTable();
            
            alert('Permanent changes saved to AllStrategyDetails.xlsx');
        } else {
            alert('Error saving permanent changes: ' + result.message);
        }
    } catch (e) {
        console.error('Error saving permanent strategy changes:', e);
        alert('Error saving permanent changes');
    }
}