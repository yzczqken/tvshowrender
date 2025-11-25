// 显示加载动画
function showLoading() {
    document.getElementById('loading').style.display = 'block';
}

// 隐藏加载动画
function hideLoading() {
    document.getElementById('loading').style.display = 'none';
}

// 显示结果
function displayResult(message) {
    document.getElementById('result').textContent = message;
}

// 显示图表
function displayChart(chartUrl) {
    const chartContainer = document.getElementById('chart-container');
    if (chartUrl) {
        chartContainer.innerHTML = `<img src="${chartUrl}" class="chart-img" alt="Charts">`;
    } else {
        chartContainer.innerHTML = '';
    }
}

// 格式化结果
// 在格式化结果的函数中，更新处理方式
function formatResults(data, title) {
    let resultText = `${title}\n\n`;

    if (data.length === 0) {
        resultText += "No results found.";
        return resultText;
    }

    data.forEach((item, index) => {
        if (typeof item === 'object') {
            // 处理字典格式的数据
            const values = Object.values(item);
            resultText += `${index + 1}. ${values.join(', ')}\n`;
        } else {
            // 处理数组格式的数据
            resultText += `${index + 1}. ${item.join(', ')}\n`;
        }
    });

    resultText += `\nTotal: ${data.length} Results`;
    return resultText;
}

// 其他函数保持不变...
// 格式化平台信息
function formatPlatforms(netflix, hulu, primeVideo, disney) {
    const platforms = [];
    if (netflix === 1 || netflix === true) platforms.push("Netflix");
    if (hulu === 1 || hulu === true) platforms.push("Hulu");
    if (primeVideo === 1 || primeVideo === true) platforms.push("Prime Video");
    if (disney === 1 || disney === true) platforms.push("Disney+");
    return platforms.length > 0 ? platforms.join(', ') : 'No available platforms';
}

// API调用函数
async function callAPI(endpoint, data) {
    showLoading();

    try {
        const response = await fetch(`/api/${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        hideLoading();

        if (result.success) {
            return result;
        } else {
            throw new Error(result.error || 'Unknown Error');
        }
    } catch (error) {
        hideLoading();
        throw error;
    }
}

// ==================== Search Title ====================

async function searchByTitle() {
    const title = document.getElementById('search-title').value;
    if (!title) {
        displayResult('Please input the keyword of the title');
        return;
    }

    try {
        const result = await callAPI('search_by_title', { title: title });

        console.log("API Response:", result);

        let resultText = `The list of TV Shows containing ${title} is as below:\n\n`;

        if (result.results.length === 0) {
            resultText += `No TV Shows containing ${title} are found`;
        } else {
            result.results.forEach((item) => {
                resultText += `${item}\n`;
            });
            resultText += `\nTotal: ${result.count} Results`;
        }

        displayResult(resultText);
        displayChart(null);
    } catch (error) {
        displayResult(`Error: ${error.message}`);
        console.error("Search error:", error);
    }
}

async function searchExactTitle() {
    const title = document.getElementById('search-exact-title').value;
    if (!title) {
        displayResult('Please input the exact Title');
        return;
    }

    try {
        const result = await callAPI('search_exact_title', { title: title });

        if (result.results.length === 0) {
            displayResult(`No TV shows with the title "${title}" are found`);
        } else {
            let resultText = `The detailed information of "${title}" :\n`;

            resultText += result.results;
            // result.results.forEach((item) => {
            //     resultText += `${item}\n`;
            // });

            displayResult(resultText);
        }
        displayChart(null);
    } catch (error) {
        displayResult(`Error: ${error.message}`);
    }
}

// ==================== Get Top Show ====================

async function getTopShowsByYear() {
    const year = document.getElementById('top-year').value;
    const ratingType = document.getElementById('top-rating-type').value;
    const k = document.getElementById('top-k').value || 10;

    if (!year) {
        displayResult('Please input a Year');
        return;
    }

    try {
        const result = await callAPI('top_shows_by_year', {
            year: parseInt(year),
            rating_type: ratingType,
            k: parseInt(k)
        });

        let resultText = `Top ${k} TV Shows on ${ratingType} Rating in ${year}:\n`;

        if (result.results.length === 0) {
            resultText += "No Results are found";
        } else {
            result.results.forEach((item) => {
                resultText += `${item}\n`;
            });
        }

        displayResult(resultText);
        displayChart(null);
    } catch (error) {
        displayResult(`Error: ${error.message}`);
    }
}

async function getTopShowsOnPlatform() {
    const year = document.getElementById('platform-top-year').value;
    const ratingType = document.getElementById('platform-rating-type').value;
    const platform = document.getElementById('platform-name').value;
    const k = document.getElementById('platform-top-k').value || 10;

    if (!year || !platform) {
        displayResult('Please input the year and platform');
        return;
    }

    try {
        const result = await callAPI('top_shows_on_platform', {
            year: parseInt(year),
            rating_type: ratingType,
            platform: platform,
            k: parseInt(k)
        });

        let resultText = `Top ${k} ${platform} TV shows on ${ratingType} in ${year}:\n\n`;

        if (result.results.length === 0) {
            resultText += "No results are found";
        } else {
            result.results.forEach((item) => {
                resultText += `${item}\n`
            });
        }

        displayResult(resultText);
        displayChart(null);
    } catch (error) {
        displayResult(`Error: ${error.message}`);
    }
}

// ==================== statistics ====================
async function getTotalInYear() {
    const year = document.getElementById('total-year').value;
    console.log('Year:', year); // Debug

    if (!year) {
        displayResult('Please input the year');
        return;
    }

    try {
        const result = await callAPI('total_in_year', { year: parseInt(year) });
        resultText = ""
        if (result.results.length === 0) {
            displayResult(`No results found`);
        } else {
            resultText += result.results;
            displayResult(resultText);
            displayChart(result.chart_url);
        }
    } catch (error) {
        displayResult(`Error: ${error.message}`);
    }
}

async function getTotalFromYearTo() {
    const year1 = document.getElementById('year-from').value;
    const year2 = document.getElementById('year-to').value;
    const platform = document.getElementById('trend-platform').value;

    if (!year1 || !year2) {
        displayResult('Please enter start year and end year');
        return;
    }

    try {
        const result = await callAPI('total_from_year_to', {
            year1: parseInt(year1),
            year2: parseInt(year2),
            platform: platform
        });


        let resultText = `${year1}-${year2} ${platform === 'All' ? 'All Platforms' : platform} Show Count Trend:\n\n`;

        if (result.results.length === 0) {
            resultText += "No data found";
        } else {
            result.results.forEach(item => {
                resultText += `${item}\n`
                // const year = item.year || 'Unknown Year';
                // const count = item.count || 0;
                // resultText += `${year}: ${count} shows\n`;
            });
        }

        displayResult(resultText);
        displayChart(result.chart_url);
    } catch (error) {
        displayResult(`Error: ${error.message}`);
    }
}

// ==================== Comparison ====================

async function getPlatformRatingComparison() {
    const year = document.getElementById('compare-year').value;
    const ratingType = document.getElementById('compare-rating-type').value;

    if (!year) {
        displayResult('Please enter a year');
        return;
    }

    try {
        const result = await callAPI('platform_rating_comparison', {
            year: parseInt(year),
            rating_type: ratingType
        });

        let resultText = `${year} ${ratingType} Average Rating Comparison by Platform:\n\n`;

        if (result.results.length === 0) {
            resultText += "No data found";
        } else {
            resultText += result.results;
        }

        displayResult(resultText);
        displayChart(null);
    } catch (error) {
        displayResult(`Error: ${error.message}`);
    }
}

// ==================== Age Group Recommendation ====================

async function getRecommendByAge() {
    const age = document.getElementById('user-age').value;

    if (!age) {
        displayResult('Please enter your age');
        return;
    }

    try {
        const result = await callAPI('recommend_by_age', { age: parseInt(age) });

        let resultText = `Highly-rated TV show recommendations suitable for age ${age}:\n\n`;

        if (result.results.length === 0) {
            resultText += "No suitable recommendations found";
        } else {
            result.results.forEach((item) => {
                resultText += `${item}\n`
            });
        }

        displayResult(resultText);
        displayChart(null);
    } catch (error) {
        displayResult(`Error: ${error.message}`);
    }
}

// ==================== Add a TV show ====================

async function addNewShow() {
    const formData = {
        Title: document.getElementById('add-title').value,
        Year: document.getElementById('add-year').value,
        IMDb: document.getElementById('add-imdb').value,
        RottenTomatoes: document.getElementById('add-rotten').value,
        Age: document.getElementById('add-age').value,
        Netflix: document.getElementById('add-netflix').checked ? 1 : 0,
        Hulu: document.getElementById('add-hulu').checked ? 1 : 0,
        PrimeVideo: document.getElementById('add-prime').checked ? 1 : 0,
        Disney: document.getElementById('add-disney').checked ? 1 : 0
    };

    if (!formData.Title || !formData.Year || !formData.IMDb || !formData.RottenTomatoes || !formData.Age) {
        displayResult('Please input all the fields');
        return;
    }

    try {
        const result = await callAPI('add_show', formData);

        if (result.success) {
            displayResult(result.message);
            document.getElementById('add-show-form').reset();
        } else {
            displayResult(`Error: ${result.error}`);
        }
    } catch (error) {
        displayResult(`Error: ${error.message}`);
    }
}

// ==================== Delete Functions ====================

// ==================== Delete Functions ====================

// ==================== Delete Functions ====================

async function deleteShow() {
    const title = document.getElementById('delete-title').value;

    if (!title) {
        displayResult('Please enter a title to delete');
        return;
    }

    const confirmation = confirm(`Are you sure you want to delete ALL shows with title: "${title}"?\n\nThis action cannot be undone!`);
    if (!confirmation) {
        displayResult('Deletion cancelled');
        return;
    }

    try {
        const result = await callAPI('delete_show', { title: title });

        if (result.success) {
            displayResult(result.message);
            // 清空表单
            document.getElementById('delete-title').value = '';
        } else {
            displayResult(`Error: ${result.error}`);
        }
    } catch (error) {
        displayResult(`Error: ${error.message}`);
    }
}


document.addEventListener('DOMContentLoaded', function() {
    displayResult('All is Ready');
});