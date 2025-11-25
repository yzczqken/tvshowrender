import pandas as pd
import numpy as np
import sqlite3
from sqlite3 import Error
import matplotlib.pyplot as plt
import io
import base64

def get_template_content(conn,k):
    with conn:
        cur_temp = conn.cursor()
        cur_temp.execute("SELECT content FROM Templates WHERE template_id = ?", (k,))
        result_template = cur_temp.fetchone()
        if result_template:
            return result_template[0]
        return None

def get_max_id(conn):
    try:
        with conn:
            sql = "SELECT MAX(ID) FROM MainInfo"
            cur = conn.cursor()
            cur.execute(sql)
            result = cur.fetchone()
            return result[0] if result[0] is not None else 0
    except Exception as e:
        print(f"get_max_id Error : {e}")
        return 0


def add_show_to_data(conn, data):
    try:
        with conn:
            max_id = get_max_id(conn)
            id_value = max_id + 1
            data["ID"] = id_value

            # 插入MainInfo表
            sql_maininfo = """
                           INSERT INTO MainInfo (ID, Title, Year)
                           VALUES (?, ?, ?) \
                           """
            cur = conn.cursor()
            cur.execute(sql_maininfo, (data["ID"], data["Title"], data["Year"]))

            # 插入Rating表
            sql_rating = """
                         INSERT INTO Rating (ID, IMDb, RottenTomatoes)
                         VALUES (?, ?, ?) \
                         """
            cur.execute(sql_rating, (data["ID"], data["IMDb"], data["RottenTomatoes"]))

            # 插入Age表
            sql_age = """
                      INSERT INTO Age (ID, Age)
                      VALUES (?, ?) \
                      """
            cur.execute(sql_age, (data["ID"], data["Age"]))

            # 插入Platforms表
            sql_platform = """
                           INSERT INTO Platforms (ID, Netflix, Hulu, PrimeVideo, Disney)
                           VALUES (?, ?, ?, ?, ?) \
                           """
            cur.execute(sql_platform, (data["ID"], data["Netflix"], data["Hulu"], data["PrimeVideo"], data["Disney"]))

            conn.commit()
            return {"success": True, "message": f"成功添加节目: {data['Title']} ({data['Year']}), ID: {data['ID']}",
                    "id": id_value}

    except Exception as e:
        return {"success": False, "error": f"添加数据错误: {e}"}


# ==================== Delete Functions ====================

def delete_tv_show(conn, title):
    try:
        cursor = conn.cursor()

        cursor.execute("BEGIN TRANSACTION")

        cursor.execute("SELECT ID FROM MainInfo WHERE Title = ?", (title,))
        ids = [row[0] for row in cursor.fetchall()]

        if not ids:
            return {"success": False, "error": f"No show found with title '{title}'"}

        deleted_count = 0
        for id in ids:
            cursor.execute("DELETE FROM Platforms WHERE ID = ?", (id,))
            cursor.execute("DELETE FROM Rating WHERE ID = ?", (id,))
            cursor.execute("DELETE FROM Age WHERE ID = ?", (id,))
            cursor.execute("DELETE FROM MainInfo WHERE ID = ?", (id,))
            deleted_count += 1

        conn.commit()
        return {"success": True, "message": f"Successfully deleted {deleted_count} show(s) with title '{title}'"}

    except Exception as e:
        conn.rollback()
        return {"success": False, "error": f"Deletion failed: {str(e)}"}

# ==================== Search ====================

def searchTitle(conn, title):
    cur = conn.cursor()
    sql = "SELECT Title, Year FROM MainInfo WHERE Title LIKE ?"
    keyword = f"%{title}%"
    cur.execute(sql, (keyword,))
    result_set = cur.fetchall()

    return result_set
    # columns = [desc[0] for desc in cur.description]
    # results = []
    # for row in result_set:
    #     row_dict = {}
    #     for i, column in enumerate(columns):
    #         row_dict[column] = row[i]
    #     results.append(row_dict)
    #
    # return results


def searchExactTitle(conn, title):
    cur = conn.cursor()
    sql = """
          SELECT MainInfo.Title, \
                 MainInfo.Year,
                 Platforms.Netflix, \
                 Platforms.Hulu, \
                 Platforms.PrimeVideo, \
                 Platforms.Disney,
                 Age.Age, \
                 Rating.IMDb, \
                 Rating.RottenTomatoes
          FROM MainInfo
                   JOIN Platforms ON MainInfo.ID = Platforms.ID
                   JOIN Age ON MainInfo.ID = Age.ID
                   JOIN Rating ON MainInfo.ID = Rating.ID
          WHERE MainInfo.Title LIKE ? \
          """
    keyword = title
    cur.execute(sql, (keyword,))
    result_set = cur.fetchall()

    return result_set

# ==================== Get TopShow ====================

def TopShowByYear(conn, year, rating_type):
    rating_column = "Rating.IMDb" if rating_type.lower() == "imdb" else "Rating.RottenTomatoes"
    cur = conn.cursor()
    sql = f"""
    SELECT MainInfo.Title,{rating_column},Platforms.Netflix,Platforms.Hulu,Platforms.PrimeVideo,Platforms.Disney
    FROM MainInfo,Rating,Platforms
    WHERE Year = ?
    AND  MainInfo.ID = Rating.ID
    AND  MainInfo.ID = Platforms.ID
    ORDER BY {rating_column} DESC
    """
    cur.execute(sql, (year,))
    result_set = cur.fetchall()
    return result_set


def TopShowOnPlatformByYear(conn, year, rating_type, platform):
    rating_column = "Rating.IMDb" if rating_type.lower() == "imdb" else "Rating.RottenTomatoes"
    if platform.lower() == "netflix":
        key = "Netflix"
    elif platform.lower() == "hulu":
        key = "Hulu"
    elif platform.lower() == "primevideo":
        key = "PrimeVideo"
    elif platform.lower() == "disney":
        key = "Disney"

    cur = conn.cursor()
    sql = f"""
    SELECT MainInfo.Title,{rating_column}
    FROM MainInfo,Rating,Platforms
    WHERE Year = ?
    AND  MainInfo.ID = Rating.ID
    AND  MainInfo.ID = Platforms.ID
    AND  Platforms.{key} = 1
    ORDER BY {rating_column} DESC
    """
    cur.execute(sql, (year,))
    result_set = cur.fetchall()
    return result_set


# ==================== Total ====================

def TotalInYear(conn, year):
    cur = conn.cursor()

    # Total
    sql_total = """SELECT Year,COUNT(*),SUM(CASE WHEN Rating.IMDB > 8.0 THEN 1 ELSE 0 END) AS high_rating_count
              FROM MainInfo,Rating
              WHERE Year = ?
              AND MainInfo.ID = Rating.ID
              GROUP BY Year
              """
    cur.execute(sql_total, [year])
    result_total = cur.fetchall()

    # platform
    sql_platform = """SELECT COUNT(*)                                           AS total_count, \
                             SUM(CASE WHEN Rating.IMDB > 8.0 THEN 1 ELSE 0 END) AS high_rating_count
                      FROM MainInfo, \
                           Platforms, \
                           Rating
                      WHERE Year = ?
                        AND MainInfo.ID = Platforms.ID
                        AND MainInfo.ID = Rating.ID
                        AND Platforms.{} = 1
                      GROUP BY Year \
                   """
    cur.execute(sql_platform.format("Netflix"), [year])
    result_netflix = cur.fetchall()
    cur.execute(sql_platform.format("Hulu"), [year])
    result_hulu = cur.fetchall()
    cur.execute(sql_platform.format("PrimeVideo"), [year])
    result_prime = cur.fetchall()
    cur.execute(sql_platform.format("Disney"), [year])
    result_disney = cur.fetchall()

    return result_total, result_netflix, result_hulu, result_prime, result_disney


def TotalFromYearAll(conn, year1, year2):
    cur = conn.cursor()
    sql_total = """SELECT Year, COUNT (*)
                   FROM MainInfo
                   WHERE Year BETWEEN ? AND ?
                   GROUP BY Year
                   ORDER BY Year ASC \
                """
    cur.execute(sql_total, [year1, year2])
    result_total = cur.fetchall()


    return result_total


def TotalFromYearOnPlatform(conn, year1, year2, platform):
    if platform.lower() == "netflix":
        key = "Netflix"
    elif platform.lower() == "hulu":
        key = "Hulu"
    elif platform.lower() == "primevideo":
        key = "PrimeVideo"
    elif platform.lower() == "disney":
        key = "Disney"

    cur = conn.cursor()
    sql_total = f"""SELECT Year,COUNT(*)
          FROM MainInfo
          WHERE Year BETWEEN ? AND ?
          AND  MainInfo.ID in (SELECT Platforms.ID
                       FROM Platforms
                       WHERE Platforms.{key} = 1
                       )
          GROUP BY Year
          ORDER BY Year ASC
    """
    cur.execute(sql_total, [year1, year2])
    result_total = cur.fetchall()

    return result_total


# ==================== Platform Compare ====================

def crossPlatformHighestAvgRatingByYear(conn, year, rating_type):
    rating_column = "Rating.IMDb" if rating_type.lower() == "imdb" else "Rating.RottenTomatoes"
    cur = conn.cursor()
    sql = f"""
    WITH PlatformsNetFlixData AS(
      SELECT ROUND(AVG({rating_column}),2) AS Value, 'Netflix' AS PlatformName
      FROM MainInfo, Rating, Platforms
      WHERE MainInfo.ID = Rating.ID
      AND  MainInfo.ID = Platforms.ID
      AND  Platforms.Netflix = 1
      AND  MainInfo.Year = ?
      AND  {rating_column} IS NOT NULL
      GROUP BY MainInfo.Year
    ),
       PlatformHuluData AS(
      SELECT ROUND(AVG({rating_column}),2) AS Value, 'Hulu' AS PlatformName
      FROM MainInfo, Rating, Platforms
      WHERE MainInfo.ID = Rating.ID
      AND  MainInfo.ID = Platforms.ID
      AND  Platforms.Hulu = 1
      AND  MainInfo.Year = ?
      AND  {rating_column} IS NOT NULL
      GROUP BY MainInfo.Year
    ),
      PlatformPrimeVideoData AS(
      SELECT ROUND(AVG({rating_column}),2) AS Value, 'PrimeVideo' AS PlatformName
      FROM MainInfo, Rating, Platforms
      WHERE MainInfo.ID = Rating.ID
      AND  MainInfo.ID = Platforms.ID
      AND  Platforms.PrimeVideo = 1
      AND  MainInfo.Year = ?
      AND  {rating_column} IS NOT NULL
      GROUP BY MainInfo.Year
    ),
      PlatformDisneyData AS(
      SELECT ROUND(AVG({rating_column}),2) AS Value, 'Disney' AS PlatformName
      FROM MainInfo, Rating, Platforms
      WHERE MainInfo.ID = Rating.ID
      AND  MainInfo.ID = Platforms.ID
      AND  Platforms.Disney = 1
      AND  MainInfo.Year = ?
      AND  {rating_column} IS NOT NULL
      GROUP BY MainInfo.Year
    ),
    allPlatformsAvgRating AS (
      SELECT Value, PlatformName FROM PlatformsNetFlixData
      UNION ALL
      SELECT Value, PlatformName FROM PlatformHuluData
      UNION ALL
      SELECT Value, PlatformName FROM PlatformPrimeVideoData
      UNION ALL
      SELECT Value, PlatformName FROM PlatformDisneyData
    )
    SELECT * FROM allPlatformsAvgRating
    ORDER BY Value DESC
    """
    cur.execute(sql, [year, year, year, year])
    result_set = cur.fetchall()

    return result_set



# ==================== Recommendation By Age ====================

def TopShowByAgeGroup(conn, ageGroup):
    placeholder = ','.join(['?' for _ in ageGroup])
    cur = conn.cursor()
    sql = f"""
    SELECT MainInfo.Title,Rating.IMDb,Platforms.Netflix,Platforms.Hulu,Platforms.PrimeVideo,Platforms.Disney
    FROM MainInfo,Age,Rating,Platforms
    WHERE MainInfo.ID = Rating.ID
    AND  MainInfo.ID = Platforms.ID
    AND  Rating.IMDb > 8.0
    AND  MainInfo.ID In (
                 SELECT Age.ID
                 FROM  AGE
                 WHERE  Age.Age IN ({placeholder})
    )
    ORDER BY RANDOM()
    LIMIT 5
    """
    cur.execute(sql, ageGroup)
    result_set = cur.fetchall()
    return result_set


# ==================== Chart_Gen ====================

def generate_bar_chart(data, title):

    names = data['names']
    values = data['values']
    high_rating = data['high_rating']

    plt.figure(figsize=(10, 6))
    p1 = plt.bar(names[0:], values, color=['#ff9999', '#99ff99', '#66b3ff', '#D6F4ED'])
    p2 = plt.bar(names[0:], high_rating, color=['#ff3333', '#33cc33', '#0066cc', '#00cc99'])
    plt.legend((p1[0], p2[0]), ('Total', 'Rating > 8.0'))
    # plt.figure(figsize=(10, 6))
    # plt.bar(names, values, color=['#8CE4FF', '#ff9999', '#99ff99', '#66b3ff', '#D6F4ED'])
    plt.title(title)
    # plt.xticks(rotation=45)
    plt.tight_layout()

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()

    return f"data:image/png;base64,{plot_url}"


def generate_line_chart(years, counts, title):

    plt.figure(figsize=(10, 6))
    plt.plot(years, counts, marker='o')
    plt.xlabel('Year')
    plt.ylabel('Total Number')
    plt.title(title)
    plt.xticks(years, rotation=45)
    plt.tight_layout()

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()

    return f"data:image/png;base64,{plot_url}"