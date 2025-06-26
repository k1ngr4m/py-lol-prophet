import services.logger.logger as logger
from services.db.remote.mysqlutil import MysqlUtil
from plugins.sol101.config.itemList import item_name
from plugins.sol101.score_cal import timestamp_to_datetime

# 初始化MysqlUtil实例，用于数据库操作
mysql = MysqlUtil()


def update_summoner_info_to_db(summoner_info, summoner_allName):
    """
    更新召唤师信息到数据库。

    :param summoner_info: 召唤师信息字典
    :param summoner_allName: 召唤师全名
    :return: 影响的行数
    """
    # 提取召唤师信息中的各个字段
    profileIconId = summoner_info.get('profileIconId')
    level = summoner_info.get('level')
    privacy = summoner_info.get('privacy')
    puuid = summoner_info.get('puuid')
    levelAndXpVersion = summoner_info.get('levelAndXpVersion')
    unnamed = summoner_info.get('unnamed')
    expToNextLevel = summoner_info.get('expToNextLevel')
    nameChangeFlag = summoner_info.get('nameChangeFlag')
    lastGameDate = timestamp_to_datetime(summoner_info.get('lastGameDate'))
    accountId = summoner_info.get('accountId')
    internalName = summoner_info.get('internalName')
    name = summoner_info.get('name')

    # 构建插入或更新的SQL语句
    sql = f"""
        INSERT INTO {mysql.tb_summoner_info_name}
        (profileIconId, level, privacy, puuid, levelAndXpVersion, unnamed, expToNextLevel, nameChangeFlag,
        lastGameDate, accountId, internalName, name, summonerAllName)
        VALUES 
        ('{profileIconId}', {level}, '{privacy}', '{puuid}', {levelAndXpVersion}, {unnamed}, {expToNextLevel}, 
        {nameChangeFlag}, '{lastGameDate}', '{accountId}', '{internalName}', '{name}', '{summoner_allName}')
        ON DUPLICATE KEY UPDATE
            profileIconId = VALUES(profileIconId),
            level = VALUES(level),
            privacy = VALUES(privacy),
            puuid = VALUES(puuid),
            levelAndXpVersion = VALUES(levelAndXpVersion),
            unnamed = VALUES(unnamed),
            expToNextLevel = VALUES(expToNextLevel),
            nameChangeFlag = VALUES(nameChangeFlag),
            lastGameDate = VALUES(lastGameDate),
            internalName = VALUES(internalName),
            name = VALUES(name),
            summonerAllname = VALUES(summonerAllname);
    """
    try:
        logger.debug(sql)
        affect_rows = mysql.sql_execute(sql)
        return affect_rows
    except Exception as e:
        logger.error(e)


def update_summoner_data_to_db(summoner_data):
    """
    更新召唤师数据到数据库。

    :param summoner_data: 召唤师数据列表
    """
    total_rows1 = 0
    total_rows2 = 0
    # 遍历每条召唤师数据
    for game_data in summoner_data:

        game = game_data  # 因为 JSON 数据是一个包含单个元素的列表

        # 提取数据
        endOfGameResult = game['endOfGameResult']
        gameCreation = game['gameCreation']
        gameDuration = game['gameDuration']
        gameEndTimestamp = game['gameEndTimestamp']
        gameId = game['gameId']
        gameMode = game['gameMode']
        gameStartTimestamp = game['gameStartTimestamp']
        dayOfWeek = game['dayOfWeek']
        gameVersion = game['gameVersion']
        participants = game.get('participants', [])  # 获取参与者列表，若不存在则为空列表

        if participants:
            for participant in participants:
                if participant:
                    assists = participant["assists"]
                    champLevel = participant["champLevel"]
                    championId = participant["championId"]
                    championName = participant['championName']
                    deaths = participant["deaths"]
                    firstBloodKill = participant["firstBloodKill"]
                    goldEarned = participant["goldEarned"]
                    item0 = participant["item0"]
                    item1 = participant["item1"]
                    item2 = participant["item2"]
                    item3 = participant["item3"]
                    item4 = participant["item4"]
                    item5 = participant["item5"]
                    item6 = participant["item6"]
                    kills = participant["kills"]
                    magicDamageDealtToChampions = participant["magicDamageDealtToChampions"]
                    magicDamageTaken = participant["magicDamageTaken"]
                    participantId = participant["participantId"]
                    physicalDamageDealtToChampions = participant["physicalDamageDealtToChampions"]
                    physicalDamageTaken = participant["physicalDamageTaken"]
                    placement = participant["placement"]
                    profileIcon = participant["profileIcon"]
                    riotIdGameName = participant["riotIdGameName"]
                    riotIdTagline = participant["riotIdTagline"]
                    summonerId = participant['summonerId']
                    summonerLevel = participant["summonerLevel"]
                    summonerName = participant['summonerName']
                    teamEarlySurrendered = participant["teamEarlySurrendered"]
                    teamId = participant["teamId"]
                    timePlayed = participant["timePlayed"]
                    totalDamageDealt = participant["totalDamageDealt"]
                    totalDamageDealtToChampions = participant["totalDamageDealtToChampions"]
                    totalDamageShieldedOnTeammates = participant["totalDamageShieldedOnTeammates"]
                    totalDamageTaken = participant["totalDamageTaken"]
                    totalHeal = participant["totalHeal"]
                    totalHealsOnTeammates = participant["totalHealsOnTeammates"]
                    totalMinionsKilled = participant["totalMinionsKilled"]
                    totalTimeSpentDead = participant["totalTimeSpentDead"]
                    trueDamageDealtToChampions = participant["trueDamageDealtToChampions"]
                    trueDamageTaken = participant["trueDamageTaken"]
                    win = participant["win"]
                    summonerAllName = participant['summonerAllName']
                    damageConversionRate = participant["challenges"]["damageConversionRate"]  # 伤害转化率
                    damagePerMinute = participant["challenges"]["damagePerMinute"]
                    damageTakenPerMinute = participant["challenges"]["damageTakenPerMinute"]  # 分均承受伤害
                    goldPerMinute = participant["challenges"]["goldPerMinute"]  # 分均经济
                    kda = participant["challenges"]["kda"]  # kda
                    isSearched = participant["isSearched"]
                    if isSearched:
                        if not mysql.check_exists(gameId, summonerName):
                            sql1 = f"""
                                     INSERT INTO {mysql.tb_summoner_data_name} (endOfGameResult, gameCreationDate, gameDuration, gameEndTimestamp, gameId, 
                                     gameMode, gameStartTimestamp, dayOfWeek, gameVersion, summonerId,summonerName,championName,
                                     assists, champLevel, championId, deaths, firstBloodKill, goldEarned,item0,item1,item2,item3,item4,item5,item6,
                                     kills,magicDamageDealtToChampions,magicDamageTaken,participantId,
                                     physicalDamageDealtToChampions,physicalDamageTaken, placement, profileIcon,riotIdGameName,
                                     riotIdTagline,summonerLevel,teamEarlySurrendered,teamId,timePlayed,
                                     totalDamageDealt, totalDamageDealtToChampions, totalDamageShieldedOnTeammates,
                                     totalDamageTaken, totalHeal, totalHealsOnTeammates, totalMinionsKilled, totalTimeSpentDead,
                                     trueDamageDealtToChampions,trueDamageTaken,win,damageConversionRate,damagePerMinute,
                                     damageTakenPerMinute,goldPerMinute,kda,isdel,summonerAllName) VALUES ('{endOfGameResult}', '{gameCreation}', {gameDuration}, '{gameEndTimestamp}', 
                                     {gameId}, '{gameMode}', '{gameStartTimestamp}', '{dayOfWeek}', '{gameVersion}', '{summonerId}',
                                     '{summonerName}','{championName}', {assists},{champLevel},{championId},{deaths}, {firstBloodKill}, {goldEarned},
                                     '{item0}','{item1}','{item2}','{item3}','{item4}','{item5}','{item6}',{kills},
                                     {magicDamageDealtToChampions},{magicDamageTaken},{participantId},
                                     {physicalDamageDealtToChampions},{physicalDamageTaken}, {placement}, '{profileIcon}',
                                     '{riotIdGameName}','{riotIdTagline}',{summonerLevel}, {teamEarlySurrendered},{teamId},{timePlayed},
                                     {totalDamageDealt}, {totalDamageDealtToChampions}, {totalDamageShieldedOnTeammates},
                                     {totalDamageTaken}, {totalHeal}, {totalHealsOnTeammates}, {totalMinionsKilled}, {totalTimeSpentDead},
                                     {trueDamageDealtToChampions},{trueDamageTaken},
                                     {win},{damageConversionRate},{damagePerMinute}, {damageTakenPerMinute}, {goldPerMinute}, {kda}, 0, '{summonerAllName}');
                                """
                            affected_rows = mysql.sql_execute(sql1)
                            total_rows1 += affected_rows

        # if participants:
        #     mysql.tb_summoner_data_name = 'tb_analysis_data'
        #     for participant in participants:
        #         if participant:
        #             assists = participant["assists"]
        #             champLevel = participant["champLevel"]
        #             championId = participant["championId"]
        #             championName = participant['championName']
        #             deaths = participant["deaths"]
        #             firstBloodKill = participant["firstBloodKill"]
        #             goldEarned = participant["goldEarned"]
        #             item0 = participant["item0"]
        #             item1 = participant["item1"]
        #             item2 = participant["item2"]
        #             item3 = participant["item3"]
        #             item4 = participant["item4"]
        #             item5 = participant["item5"]
        #             item6 = participant["item6"]
        #             kills = participant["kills"]
        #             magicDamageDealtToChampions = participant["magicDamageDealtToChampions"]
        #             magicDamageTaken = participant["magicDamageTaken"]
        #             participantId = participant["participantId"]
        #             physicalDamageDealtToChampions = participant["physicalDamageDealtToChampions"]
        #             physicalDamageTaken = participant["physicalDamageTaken"]
        #             placement = participant["placement"]
        #             profileIcon = participant["profileIcon"]
        #             riotIdGameName = participant["riotIdGameName"]
        #             riotIdTagline = participant["riotIdTagline"]
        #             spell1Casts = participant["spell1Casts"]
        #             spell2Casts = participant["spell2Casts"]
        #             spell3Casts = participant["spell3Casts"]
        #             spell4Casts = participant["spell4Casts"]
        #             summoner1Casts = participant["summoner1Casts"]
        #             summoner2Casts = participant["summoner2Casts"]
        #             summonerId = participant['summonerId']
        #             summonerLevel = participant["summonerLevel"]
        #             summonerName = participant['summonerName']
        #             teamEarlySurrendered = participant["teamEarlySurrendered"]
        #             teamId = participant["teamId"]
        #             timePlayed = participant["timePlayed"]
        #             totalDamageDealt = participant["totalDamageDealt"]
        #             totalDamageDealtToChampions = participant["totalDamageDealtToChampions"]
        #             totalDamageShieldedOnTeammates = participant["totalDamageShieldedOnTeammates"]
        #             totalDamageTaken = participant["totalDamageTaken"]
        #             totalHeal = participant["totalHeal"]
        #             totalHealsOnTeammates = participant["totalHealsOnTeammates"]
        #             totalMinionsKilled = participant["totalMinionsKilled"]
        #             totalTimeSpentDead = participant["totalTimeSpentDead"]
        #             trueDamageDealtToChampions = participant["trueDamageDealtToChampions"]
        #             trueDamageTaken = participant["trueDamageTaken"]
        #             win = participant["win"]
        #             summonerAllName = participant['summonerAllName']
        #             damageConversionRate = participant["challenges"]["damageConversionRate"]  # 伤害转化率
        #             damagePerMinute = participant["challenges"]["damagePerMinute"]
        #             damageTakenPerMinute = participant["challenges"]["damageTakenPerMinute"]  # 分均承受伤害
        #             goldPerMinute = participant["challenges"]["goldPerMinute"]  # 分均经济
        #             kda = participant["challenges"]["kda"]  # kda
        #             if not mysql.check_exists(gameId, summonerName):
        #                 sql2 = f"""
        #                          INSERT INTO {mysql.tb_summoner_data_name} (endOfGameResult, gameCreationDate, gameDuration, gameEndTimestamp, gameId,
        #                          gameMode, gameStartTimestamp, dayOfWeek, gameVersion, summonerId,summonerName,championName,
        #                          assists, champLevel, championId, deaths, firstBloodKill, goldEarned,item0,item1,item2,item3,item4,item5,item6,
        #                          kills,magicDamageDealtToChampions,magicDamageTaken,participantId,
        #                          physicalDamageDealtToChampions,physicalDamageTaken, placement, profileIcon,riotIdGameName,
        #                          riotIdTagline,spell1Casts,spell2Casts,spell3Casts,spell4Casts,
        #                          summoner1Casts,summoner2Casts,summonerLevel,teamEarlySurrendered,teamId,timePlayed,
        #                          totalDamageDealt, totalDamageDealtToChampions, totalDamageShieldedOnTeammates,
        #                          totalDamageTaken, totalHeal, totalHealsOnTeammates, totalMinionsKilled, totalTimeSpentDead,
        #                          trueDamageDealtToChampions,trueDamageTaken,win,damageConversionRate,damagePerMinute,
        #                          damageTakenPerMinute,goldPerMinute,kda,isdel,summonerAllName) VALUES ('{endOfGameResult}', '{gameCreation}', {gameDuration}, '{gameEndTimestamp}',
        #                          {gameId}, '{gameMode}', '{gameStartTimestamp}', '{dayOfWeek}', '{gameVersion}', '{summonerId}',
        #                          '{summonerName}','{championName}', {assists},{champLevel},{championId},{deaths}, {firstBloodKill}, {goldEarned},
        #                          '{item0}','{item1}','{item2}','{item3}','{item4}','{item5}','{item6}',{kills},
        #                          {magicDamageDealtToChampions},{magicDamageTaken},{participantId},
        #                          {physicalDamageDealtToChampions},{physicalDamageTaken}, {placement}, '{profileIcon}',
        #                          '{riotIdGameName}','{riotIdTagline}', {spell1Casts},{spell2Casts},{spell3Casts},{spell4Casts},
        #                          {summoner1Casts},{summoner2Casts},{summonerLevel}, {teamEarlySurrendered},{teamId},{timePlayed},
        #                          {totalDamageDealt}, {totalDamageDealtToChampions}, {totalDamageShieldedOnTeammates},
        #                          {totalDamageTaken}, {totalHeal}, {totalHealsOnTeammates}, {totalMinionsKilled}, {totalTimeSpentDead},
        #                          {trueDamageDealtToChampions},{trueDamageTaken},
        #                          {win},{damageConversionRate},{damagePerMinute}, {damageTakenPerMinute}, {goldPerMinute}, {kda}, 0, '{summonerAllName}');
        #                     """
        #                 affected_rows = mysql.sql_execute(sql2)
        #                 total_rows2 += affected_rows
    return total_rows1, total_rows2


def fetch_summoner_info():
    """
    获取召唤师信息。
    """
    sql = f"select puuid, accountId, summonerAllName from {mysql.tb_summoner_info_name} order by isfriend desc"
    try:
        res = list(mysql.get_fetchall(sql))
        logger.info(res)
        return res
    except Exception as e:
        logger.error(e)


def replace_itemName():
    """
    替换装备名称。
    """
    for i in range(0, 7):
        tb_item_name = f'item{i}'

        sql = f"select DISTINCT {tb_item_name} from {mysql.tb_summoner_data_name};"
        res = list(mysql.get_fetchall(sql))
        print(res)

        for result in res:
            item0_value = result[f'{tb_item_name}']
            try:
                items_name = item_name[str(item0_value)]['name']
                sql1 = f"update {mysql.tb_summoner_data_name} set {tb_item_name} = '{items_name}' where {tb_item_name} = '{item0_value}';"
                print(sql1)
                affected_rows = mysql.sql_execute(sql1)
                print(affected_rows)
            except Exception as e:
                print(e)


def replace_champAttr():
    """
    替换英雄属性。
    """
    sql = f"select DISTINCT championName from {mysql.tb_summoner_info_name} where gameMode = 'ARAM';"
    res = list(mysql.get_fetchall(sql))
    try:
        for i in res:
            champion_name = i['championName']
            sql2 = f"select Attributes from tb_champion_info where nameZh = '{champion_name}'"
            res2 = mysql.get_fetchall(sql2)
            for j in res2:
                attributes = j['Attributes']
                if ' • ' in attributes:
                    attr1, attr2 = str(attributes).split(' • ')
                else:
                    attr1 = attributes
                    attr2 = ""
                sql3 = f"update tb_champion_info set Attributes1 = '{attr1}', Attributes2 = '{attr2}' where NameZh = '{champion_name}';"
                logger.info(sql3)
                mysql.sql_execute(sql3)
    except Exception as e:
        print(e)


if __name__ == '__main__':
    # replace_itemName()    # 替换装备名称
    # replace_champAttr()   # 替换英雄属性
    fetch_summoner_info()
