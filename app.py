import pool
from flask import Flask, render_template, request, jsonify, g
import sqlite3
import os
from tv_analysis import *

#pool = ConnectionPool('TVshows.db', max_connections=10)
app = Flask(__name__)
DATABASE = 'TVshows.db'


def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = sqlite3.connect(DATABASE, check_same_thread=False)
        g.sqlite_db.row_factory = sqlite3.Row
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


@app.route('/')
def index():
    return render_template('index.html')

# 必須添加這部分
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
# ==================== API ====================

# Search
@app.route('/api/search_by_title', methods=['POST'])
def api_search_by_title():
    db = get_db()
    data = request.get_json()
    title = data.get('title')

    if not title:
        return jsonify({'success': False, 'error': 'Please input the keyword of the title'})

    try:
        results = searchTitle(db, title)
        template_content = get_template_content(db,1)
        i = 1
        formatted_texts = []
        if(len(results)>0):
            for result in results:
                formatted_text = eval(f"f'{template_content}'")
                formatted_texts.append(formatted_text)
                i = i + 1
        return jsonify({
            'success': True,
            'results': formatted_texts,
            'count': len(results)
        })
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/search_exact_title', methods=['POST'])
def api_search_exact_title():
    db = get_db()
    data = request.get_json()
    title = data.get('title')

    if not title:
        return jsonify({'success': False, 'error': 'Please input the exact title'})

    try:
        result = searchExactTitle(db, title)
        template_content = get_template_content(db,2)
        result = result[0]
        platforms = []
        if result[2] == 1:
             platforms.append("Netflix")
        if result[3] == 1:
            platforms.append("Hulu")
        if result[4] == 1:
            platforms.append("PrimeVideo")
        if result[5] == 1:
            platforms.append("Disney+")
        platform = ", ".join(platforms)
        if(len(result)>0):
            formatted_text = eval(f"f'{template_content}'")
        return jsonify({
            'success': True,
            'results': formatted_text,
            'count': len(result)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# Get TopShow
@app.route('/api/top_shows_by_year', methods=['POST'])
def api_top_shows_by_year():
    db = get_db()
    data = request.get_json()
    year = data.get('year')
    rating_type = data.get('rating_type', 'IMDb')
    k = data.get('k', 10)

    if not year:
        return jsonify({'success': False, 'error': 'Please input a year'})

    try:
        results = TopShowByYear(db, int(year), rating_type)
        template_content = get_template_content(db, 3)
        results = results[:k]
        formatted_texts = []
        i = 0
        for result in results:
            platforms = []
            if result[2] == 1:
                platforms.append("Netflix")
            if result[3] == 1:
                platforms.append("Hulu")
            if result[4] == 1:
                platforms.append("PrimeVideo")
            if result[5] == 1:
                platforms.append("Disney+")
            platform = ", ".join(platforms)
            formatted_text = eval(f"f'{template_content}'")
            formatted_texts.append(formatted_text)
            i = i + 1
        return jsonify({
            'success': True,
            'results': formatted_texts,
            'count': len(results)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/top_shows_on_platform', methods=['POST'])
def api_top_shows_on_platform():
    db = get_db()
    data = request.get_json()
    year = data.get('year')
    rating_type = data.get('rating_type', 'IMDb')
    platform = data.get('platform')
    k = data.get('k', 10)

    if not year or not platform:
        return jsonify({'success': False, 'error': 'Please input the year and platform'})

    try:
        results = TopShowOnPlatformByYear(db, int(year), rating_type, platform)
        template_content = get_template_content(db, 4)
        results = results[:k]
        formatted_texts = []
        i = 0
        for result in results:
            formatted_text = eval(f"f'{template_content}'")
            formatted_texts.append(formatted_text)
            i = i + 1
        return jsonify({
            'success': True,
            'results': formatted_texts,
            'count': len(results)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# Total Count
@app.route('/api/total_in_year', methods=['POST'])
def api_total_in_year():
    db = get_db()
    data = request.get_json()
    year = data.get('year')

    if not year:
        return jsonify({'success': False, 'error': 'Please input the Year'})

    try:
        total, netflix, hulu, prime, disney = TotalInYear(db, int(year))
        template_content = get_template_content(db, 5)
        formatted_text = eval(f"f'{template_content}'")
        if total:
            chart_data = {
                'names': ['Total', 'Netflix', 'Hulu', 'Prime Video', 'Disney+'],
                'values': [
                    total[0][1] if total else 0,
                    netflix[0][0] if netflix else 0,
                    hulu[0][0] if hulu else 0,
                    prime[0][0] if prime else 0,
                    disney[0][0] if disney else 0
                ],
                'high_rating':[
                    total[0][2] if total else 0,
                    netflix[0][1] if netflix else 0,
                    hulu[0][1] if hulu else 0,
                    prime[0][1] if prime else 0,
                    disney[0][1] if disney else 0
                ]
            }
            chart_url = generate_bar_chart(chart_data, f'Statistics on each platform in {year} ')
        else:
            chart_url = None

        return jsonify({
            'success': True,
            'results': formatted_text,
            'chart_url': chart_url
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/total_from_year_to', methods=['POST'])
def api_total_from_year_to():
    db = get_db()
    data = request.get_json()
    year1 = data.get('year1')
    year2 = data.get('year2')
    platform = data.get('platform', 'All')

    if not year1 or not year2:
        return jsonify({'success': False, 'error': 'Please input the start year and end year'})

    try:
        if platform == 'All':
            results = TotalFromYearAll(db, int(year1), int(year2))
        else:
            results = TotalFromYearOnPlatform(db, int(year1), int(year2), platform)
        template_content = get_template_content(db, 6)
        formatted_texts = []
        years = []
        counts = []
        if results:
            for result in results:
                formatted_text = eval(f"f'{template_content}'")
                formatted_texts.append(formatted_text)
                # counts = [result['count'] for result in results]
                # years = [result['year'] for result in results]
                years.append(result[0])
                counts.append(result[1])
            # platform = 'All platform' if platform == 'All' else platform
            chart_url = generate_line_chart(years, counts, f'{year1}-{year2} Trend of Total number on ({platform})')
        else:
            chart_url = None

        return jsonify({
            'success': True,
            'results': formatted_texts,
            'count': len(results),
            'chart_url': chart_url
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# Comparison
@app.route('/api/platform_rating_comparison', methods=['POST'])
def api_platform_rating_comparison():
    db = get_db()
    data = request.get_json()
    year = data.get('year')
    rating_type = data.get('rating_type', 'IMDb')

    if not year:
        return jsonify({'success': False, 'error': 'Please input a year'})

    try:
        results = crossPlatformHighestAvgRatingByYear(db, int(year), rating_type)
        template_content = get_template_content(db, 7)
        searchResult=results
        formatted_text = eval(f"f'{template_content}'")
        return jsonify({
            'success': True,
            'results': formatted_text,
            'count': len(results)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# Age Recommendation
@app.route('/api/recommend_by_age', methods=['POST'])
def api_recommend_by_age():
    db = get_db()
    data = request.get_json()
    age = data.get('age')

    if not age:
        return jsonify({'success': False, 'error': '请输入年龄'})

    try:
        age = int(age)
        if age >= 18:
            ageGroup = ['18+', '16+', '13+', '7+', 'All']
        elif age >= 16:
            ageGroup = ['16+', '13+', '7+', 'All']
        elif age >= 13:
            ageGroup = ['13+', '7+', 'All']
        elif age >= 7:
            ageGroup = ['7+', 'All']
        else:
            ageGroup = ['All']

        results = TopShowByAgeGroup(db, ageGroup)
        template_content = get_template_content(db, 8)
        formatted_texts = []
        i = 1
        for result in results:
            platforms = []
            if result[2] == 1:
                platforms.append("Netflix")
            if result[3] == 1:
                platforms.append("Hulu")
            if result[4] == 1:
                platforms.append("PrimeVideo")
            if result[5] == 1:
                platforms.append("Disney+")
            platform = ", ".join(platforms)
            formatted_text = eval(f"f'{template_content}'")
            formatted_texts.append(formatted_text)
            i = i + 1
        return jsonify({
            'success': True,
            'results': formatted_texts,
            'count': len(results)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# Add show
@app.route('/api/add_show', methods=['POST'])
def api_add_show():
    db = get_db()
    data = request.get_json()

    required_fields = ['Title', 'Year', 'IMDb', 'RottenTomatoes', 'Age', 'Netflix', 'Hulu', 'PrimeVideo', 'Disney']
    for field in required_fields:
        if field not in data:
            return jsonify({'success': False, 'error': f'Lack of: {field}'})

    try:
        result = add_show_to_data(db, data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# Delete show
@app.route('/api/delete_show', methods=['POST'])
def api_delete_show():
    db = get_db()
    data = request.get_json()
    title = data.get('title')

    if not title:
        return jsonify({'success': False, 'error': 'Please input the title of the TV show you want to delete'})

    try:
        result = delete_tv_show(db, title)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


if __name__ == '__main__':
    app.run(debug=True, threaded=True)