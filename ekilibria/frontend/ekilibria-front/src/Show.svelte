
<script>
    import { onMount } from 'svelte';
    import { userSession } from './lib/userSession.js';
    import * as echarts from 'echarts';
    import { Circle2 } from 'svelte-loading-spinners'; 

    let chartInstance;
    let gaugeInstance;
    let chartData = [];
    let burnoutIndex = 0;
    let details = {};
    let contributions = {};
    let loading = false;
    
    async function week_info() {
        // Show loading div and hide other elements
        loading = true;
        document.getElementById('details').style.display = 'none';
        document.getElementById('graphs').style.display = 'none';

        if($userSession.login_method == "google"){
            const response = await fetch('/extract_features_google/');
            if (response.ok) {
                const data = await response.json();
                console.log('Data received:', data);
                burnoutIndex = data.burnout || 0;
                contributions = data.contributions || {};
                chartData = Object.entries(contributions).map(([feature, value]) => ({ name: feature, value }));
                details = data.features || {};
                updateChart();
                updateGauge();
                updateDetails();
            } else {
                console.error('Failed to fetch burn out index for week');
            }
        }else if($userSession.login_method == "microsoft"){
            const response = await fetch('/extract_features_microsoft/');
            if (response.ok) {
                const data = await response.json();
                console.log('Data received:', data);
                burnoutIndex = data.burnout || 0;
                contributions = data.contributions || {};
                chartData = Object.entries(contributions).map(([feature, value]) => ({ name: feature, value }));
                details = data.features || {};
                updateChart();
                updateGauge();
                updateDetails();
            } else {
                console.error('Failed to fetch burn out index for week');
            }
        }
        
        // Hide loading div
        loading = false;
    }

    function updateChart() {
        // Show the details div and graphs
        document.getElementById('details').style.display = 'flex';
        document.getElementById('graphs').style.display = 'flex';

        if (!echarts.getInstanceByDom(document.getElementById('echarts-bar'))) {
            chartInstance = echarts.init(document.getElementById('echarts-bar'));
        } else {
            chartInstance = echarts.getInstanceByDom(document.getElementById('echarts-bar'));
        }
        if (!chartInstance) return;
        const option = {
            title: {
                text: 'Contributions Breakdown',
                left: 'center'
            },
            tooltip: {},
            xAxis: {
                type: 'value'
            },
            yAxis: {
                type: 'category',
                data: chartData.map(item => item.name)
            },
            series: [
                {
                    data: chartData.map(item => item.value),
                    type: 'bar',
                    itemStyle: {
                        color: '#5470C6'
                    }
                }
            ]
        };
        chartInstance.setOption(option);
    }

    function updateGauge() {
        if (!echarts.getInstanceByDom(document.getElementById('echarts-gauge'))) {
            gaugeInstance = echarts.init(document.getElementById('echarts-gauge'));
        } else {
            gaugeInstance = echarts.getInstanceByDom(document.getElementById('echarts-gauge'));
        }
        if (!gaugeInstance) return;
        const option = {
            series: [
                {
                type: 'gauge',
                startAngle: 180,
                endAngle: 0,
                center: ['50%', '75%'],
                radius: '90%',
                min: 0,
                max: 10,
                splitNumber: 8,
                axisLine: {
                    lineStyle: {
                    width: 6,
                    color: [
                        [0.25, '#7CFFB2'],
                        [0.5, '#58D9F9'],
                        [0.75, '#FDDD60'],
                        [1, '#FF6E76']
                    ]
                    }
                },
                pointer: {
                    icon: 'path://M12.8,0.7l12,40.1H0.7L12.8,0.7z',
                    length: '12%',
                    width: 20,
                    offsetCenter: [0, '-60%'],
                    itemStyle: {
                    color: 'auto'
                    }
                },
                axisTick: {
                    length: 12,
                    lineStyle: {
                    color: 'auto',
                    width: 2
                    }
                },
                splitLine: {
                    length: 20,
                    lineStyle: {
                    color: 'auto',
                    width: 5
                    }
                },
                axisLabel: {
                    color: '#464646',
                    fontSize: 20,
                    distance: -60,
                    rotate: 'tangential',
                    formatter: function (value) {
                    if (value === 8.75) {
                        return 'Burned';
                    } else if (value === 6.25) {
                        return 'Risky';
                    } else if (value === 3.75) {
                        return 'Balanced';
                    } else if (value === 1.25) {
                        return 'Healthy';
                    }
                    return '';
                    }
                },
                title: {
                    offsetCenter: [0, '-10%'],
                    fontSize: 20
                },
                detail: {
                    fontSize: 30,
                    offsetCenter: [0, '-35%'],
                    valueAnimation: true,
                    formatter: function (value) {
                        return value.toFixed(2);
                    },
                    color: 'inherit'
                },
                data: [
                    {
                    value: burnoutIndex,
                    name: 'Burn Out Index'
                    }
                ]
                }
            ]
            };
        gaugeInstance.setOption(option);
    }

    function updateDetails() {
        const detailsDiv = document.getElementById('details');
        let result = '<p style="font-weight: bold; text-align: center;">Details</p>'; 
        
        if(Object.keys(details).length > 0){
            result += '<div style="display: flex; justify-content: center; align-items: center; margin-top: 1em;">';
            result += '<table style="border-collapse: collapse; min-width: 250px;">';
            result += '<thead><tr><th style="border: 1px solid #ccc; padding: 4px 8px;">Feature</th>';
            result += '<th style="border: 1px solid #ccc; padding: 4px 8px;">Value</th></tr></thead>';
            result += '<tbody>';
            for (const [feature, value] of Object.entries(details).reverse()) {
                result += `<tr><td style="border: 1px solid #ccc; padding: 4px 8px;">${feature}</td>`;
                result += `<td style="border: 1px solid #ccc; padding: 4px 8px;">${value.toFixed(2)}</td></tr>`;
            }
            result += '</tbody></table></div>';
        } else {
            result += '<div style="text-align: center;">No details available</div>';
        }
        detailsDiv.innerHTML = result;
    }


    
</script>

<div class="container">
    <h2>Welcome {$userSession.user_email}</h2>
    <p>Do you want to calculate the burn out index of this week, month or year</p>
    <button class="display-info" on:click={() => week_info()}>Week</button>
    <button class="display-info" on:click={() => console.log('Burn out index for month')}>Month</button>
    <button class="display-info" on:click={() => console.log('Burn out index for year')}>Year</button>

    <div id="info" style="display: flex; flex-wrap: wrap; justify-content: center; align-items: flex-start; gap: 2em;">
        {#if loading}
            <div id="loading" style="display: flex; justify-content: center; align-items: center; width: 100%; height: 100vh;">
                <Circle2 size="200" colorOuter="#007BFF" colorCenter="#007BFF" colorInner="#007BFF" />
            </div>
        {/if}
        <div id="graphs" style="display: flex; flex-direction: row; gap: 2em; align-items: flex-start;">
            <div id="echarts-gauge" style="width: 350px; height: 300px;"></div>
            <div id="echarts-bar" style="width: 500px; height: 400px;"></div>
        </div>
        <div id="details"></div>
    </div>
</div>


