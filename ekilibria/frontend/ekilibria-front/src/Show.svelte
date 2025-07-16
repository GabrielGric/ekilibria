
<script>
    import { onMount } from 'svelte';
    import { userSession } from './lib/userSession.js';
    import * as echarts from 'echarts';
    import { Circle2 } from 'svelte-loading-spinners'; 
    import Icon from 'svelte-awesome/components/Icon.svelte';
    import { calendar, calendarO,calendarCheckO } from 'svelte-awesome/icons';

    let chartInstance;
    let gaugeInstance;
    let chartData = [];
    let burnoutIndex = 0;
    let details = {};
    let contributions = {};
    let loading = false;
    let weeks = [];
    let weeksFeatures = [];
    let weekFrom = '';
    let weekTo = '';
    let weekInfo = {};
    const features_display = {
        'num_events': "Meetings",
        'num_events_outside_hours': "Meetings Outside Hours",
        'total_meeting_hours': "Total Meeting Hours",
        'avg_meeting_duration': "Average Meeting Duration",
        'meetings_weekend': "Weekend Meetings",
        'emails_sent': "Emails Sent",
        'emails_sent_out_of_hours': "Emails Sent Out of Hours",
        'docs_created': "Documents Created",
        'docs_edited': "Documents Edited",
        'num_meetings_no_breaks': "Meetings Without Breaks",
        'emails_received': "Emails Received",
        'num_overlapping_meetings': "Overlapping Meetings"
    };
    
    async function week_info() {
        // Show loading div and hide other elements
        loading = true;
        document.getElementById('details').style.display = 'none';
        document.getElementById('graphs').style.display = 'none';
        document.getElementById('echarts-line').style.display = 'none';
        // Deactivate buttons to prevent multiple clicks
        deactivateButtons();
        console.log('Fetching data for week info');
        let result = [];
        if($userSession.login_method == "google"){
            console.log('Fetching data for Google user');
            const response = await fetch('/extract_features_google_new/1');
            if (response.ok) {
                const data = await response.json();
                result = data;
                console.log('Data received:', data); 
            } else {
                console.error('Failed to fetch burn out index for week');
            }
        }else if($userSession.login_method == "microsoft"){
            const response = await fetch('/extract_features_microsoft_new/1');
            if (response.ok) {
                const data = await response.json();
                result = data;
                console.log('Data received:', data);
            } else {
                console.error('Failed to fetch burn out index for week');
            }
        }else {
            console.error('Unsupported login method:', $userSession.login_method);
            loading = false;
            return;
        }
        let prediction = result[0]["result"][0];
        let features = result[1];
        burnoutIndex = prediction.burnout_index || 0;
        contributions = prediction.contributions || {};
        chartData = Object.entries(contributions).map(([feature, value]) => ({ name: feature, value }));
        details = features[0];
        weekFrom = prediction.fecha_desde || '';
        weekTo = prediction.fecha_hasta || '';
        updateChart();
        updateGauge();
        updateDetails();
        updateDates();
        
        // Hide loading div
        loading = false;
        // Activate buttons after data is loaded
        activateButtons();
    }

    async function multiple_week_info(numWeeks){
        // Show loading div and hide other elements
        loading = true;
        document.getElementById('details').style.display = 'none';
        document.getElementById('graphs').style.display = 'none';
        deactivateButtons();

        if($userSession.login_method == "google"){
            const response = await fetch('/extract_features_google_new/' + numWeeks);
            if (response.ok) {
                const data = await response.json();
                console.log('Data received:', data);
                weeks = data[0].result;
                weeksFeatures = data[1];
                updateLineChart();
            } else {
                console.error('Failed to fetch burn out index for week');
            }
        }else if($userSession.login_method == "microsoft"){
            const response = await fetch('/extract_features_microsoft_new/'+ numWeeks);
            if (response.ok) {
                const data = await response.json();
                console.log('Data received:', data);
                weeks = data[0].result;
                weeksFeatures = data[1];
                updateLineChart();
            } else {
                console.error('Failed to fetch burn out index for week');
            }
        }
        
        // Hide loading div
        loading = false;
        // Activate buttons after data is loaded
        activateButtons();
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
                data: chartData.map(item => features_display[item.name] || item.name)
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
                        [0.25, '#B2FFA9'],
                        [0.5, '#1B9AAA'],
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

    function updateLineChart(){
        console.log(weeks);
        document.getElementById('echarts-line').style.display = 'block';
        if (!echarts.getInstanceByDom(document.getElementById('echarts-line'))) {
            chartInstance = echarts.init(document.getElementById('echarts-line'));
        } else {
            chartInstance = echarts.getInstanceByDom(document.getElementById('echarts-line'));
        }
        const option = {
            xAxis: {
                type: 'category',
                data: weeks.map((week, index) => `Week ${index + 1}`),
            },
            yAxis: {
                type: 'value'
            },
            tooltip: {
                trigger: 'axis',
                formatter: function(params) {
                    const weekIndex = params[0].dataIndex;
                    const weekData = weeks[weekIndex];
                    return `Week ${weekIndex + 1}: ${weekData.fecha_desde} to ${weekData.fecha_hasta}<br>Burnout Index: ${weekData.burnout_index}`;
                }
            },
            series: [
                {
                data: weeks.map(week => week.burnout_index),
                type: 'line',
                symbol: 'circle',
                symbolSize: 20,
                lineStyle: {
                    color: '#5470C6',
                    width: 4,
                    type: 'dashed'
                },
                itemStyle: {
                    borderWidth: 3,
                    borderColor: '#EE6666',
                    color: 'yellow'
                }
                }
            ]
        };
        chartInstance.setOption(option);

        // Register click event on data points
        chartInstance.off('click'); // Remove previous listeners to avoid duplicates
        chartInstance.on('click', function(params) {
            if (params.componentType === 'series' && params.seriesType === 'line') {
                const weekIndex = params.dataIndex;
                const weekData = weeks[weekIndex];
                const weekFeatures = weeksFeatures[weekIndex] || {};
                console.log('Clicked week data:', weekData);
                console.log('Clicked week features:', weekFeatures);
                burnoutIndex = weekData.burnout_index || 0;
                contributions = weekData.contributions || {};
                chartData = Object.entries(contributions).map(([feature, value]) => ({ name: feature, value }));
                details = weekFeatures;
                weekFrom = weekData.fecha_desde || '';
                weekTo = weekData.fecha_hasta || ''; 
                updateChart();
                updateGauge();
                updateDetails();
                updateDates();

            }
        });               
    }

    function updateDetails() {
        const detailsDiv = document.getElementById('details');
        let result = ''; 
        
        if(Object.keys(details).length > 0){
            result += '<div style="display: flex; justify-content: center; align-items: center; margin-top: 1em;">';
            result += '<table style="border-collapse: collapse; min-width: 250px;">';
            result += '<thead><tr><th style="border: 1px solid #ccc; padding: 4px 8px;">Feature</th>';
            result += '<th style="border: 1px solid #ccc; padding: 4px 8px;">Value</th></tr></thead>';
            result += '<tbody>';
            for (const [feature, value] of Object.entries(details).reverse()) {
                if(feature === 'fecha_desde' || feature === 'fecha_hasta') continue; // Skip date fields
                result += `<tr><td style="border: 1px solid #ccc; padding: 4px 8px;">${features_display[feature]}</td>`;
                result += `<td style="border: 1px solid #ccc; padding: 4px 8px;">${value}</td></tr>`;
            }
            result += '</tbody></table></div>';
        } else {
            result += '<div style="text-align: center;">No details available</div>';
        }
        detailsDiv.innerHTML = result;
    }

    function updateDates() {
        const weekFromEle = document.getElementById('week_from');
        weekFromEle.innerHTML = `Week from: ${weekFrom} to ${weekTo}`;
        weekFromEle.style.display = 'block';
    }

    function deactivateButtons() {
        document.querySelectorAll('button.display-info').forEach(elem => {
            console.log('Disabling button:', elem);
            elem.disabled = true;
            elem.style.cursor = 'not-allowed';
            elem.style.opacity = '0.5';
        });
    }

    function activateButtons() {
        document.querySelectorAll('button.display-info').forEach(elem => {
            elem.disabled = false;
            elem.style.cursor = 'pointer';
            elem.style.opacity = '1';
        });
    }

    onMount(async () => {
        const response = await fetch('/get_login_method');
        if (response.ok) {
            const data = await response.json();
            userSession.update(session => ({
            ...session,
            login_method: data.login_method
            }));
        }

        const userResponse = await fetch('/get_login_user_email');
        if (userResponse.ok) {
            const userData = await userResponse.json();
            userSession.update(session => ({
            ...session,
            user_email: userData.user_name || 'Unknown User'
            }));
        } else {
            console.error('Failed to fetch user email');
            userSession.update(session => ({
            ...session,
            user_email: 'Unknown User'
            }));
        }
    });
    
</script>
<div class="container">
    <h1>Welcome {$userSession.user_email}</h1>
    <button class="display-info" on:click={() => week_info()}>
        Week <Icon data={calendar} />
    </button>
    <button class="display-info" on:click={() => multiple_week_info(4)}>
        Month <Icon data={calendarO} />
    </button>
    <button class="display-info" on:click={() => multiple_week_info(12)}>
        Year <Icon data={calendarCheckO} />
    </button>

    <div id="info" style="display: flex; flex-wrap: wrap; justify-content: center; align-items: flex-start; gap: 2em;">
        {#if loading}
            <div id="loading" style="display: flex; justify-content: center; align-items: center; width: 100%; height: 100vh;">
                <Circle2 size="200" colorOuter="#2E4052" colorCenter="#2E4052" colorInner="#2E4052" />
            </div>
        {/if}
        <h3 id="week_from" style="display: none; width:100%"></h3>
        
        <div id="graphs" style="display: flex; flex-direction: row; gap: 2em; align-items: flex-start;">
            <div id="echarts-gauge" style="width: 350px; height: 300px;"></div>
            <div id="echarts-bar" style="width: 500px; height: 400px;"></div>
        </div>
        <div id="echarts-line" style="width: 500px; height: 400px; display:none"></div>
        <div id="details"></div>
    </div>
</div>


