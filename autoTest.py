# -*- coding: UTF-8 -*-
import os, time, random
import sys, io
import tanks, pygame
import threading
import logging

from pygame.locals import *


def test():
    pass


def turnAround(player):
    """ Turn tank into another random direction """
    if player.direction == player.DIR_UP:
        player.rotate(player.direction + random.choice([1, 2, 3]), False)
    elif player.direction == player.DIR_RIGHT:
        player.rotate(player.direction + random.choice([-1, 1, 2]), False)
    elif player.direction == player.DIR_DOWN:
        player.rotate(player.direction + random.choice([-2, -1, 1]), False)
    elif player.direction == player.DIR_LEFT:
        player.rotate(player.direction + random.choice([-3, -2, -1]), False)


def autoMove(player):
    """Auto move player"""
    if player.direction == player.DIR_UP:
        new_position = [player.rect.left, player.rect.top - player.speed]
        if new_position[1] < 0:
            turnAround(player)
            return

    elif player.direction == player.DIR_RIGHT:
        new_position = [player.rect.left + player.speed, player.rect.top]
        if new_position[0] > (416 - 26):
            turnAround(player)
            return

    elif player.direction == player.DIR_DOWN:
        new_position = [player.rect.left, player.rect.top + player.speed]
        if new_position[1] > (416 - 26):
            turnAround(player)
            return

    elif player.direction == player.DIR_LEFT:
        new_position = [player.rect.left - player.speed, player.rect.top]
        if new_position[0] < 0:
            turnAround(player)
            return
    player_rect = pygame.Rect(new_position, [26, 26])

    # collisions with tiles
    if player_rect.collidelist(player.level.obstacle_rects) != -1:
        turnAround(player)
        return

    # collisions with other players
    for pl in tanks.players:
        if pl != player and pl.state == pl.STATE_ALIVE and player_rect.colliderect(pl.rect):
            turnAround(player)
            return

    # collisions with enemies
    for enemy in tanks.enemies:
        if player_rect.colliderect(enemy.rect):
            turnAround(player)
            return

    # collisions with bonuses
    for bonus in tanks.bonuses:
        if player_rect.colliderect(bonus.rect) == True:
            player.bonus = bonus

    player.rotate(player.direction)
    player.rect.topleft = (new_position[0], new_position[1])


def autoFire (player):
    """Tank auto shot when meet enemy"""
    isFire = True
    steel_tile = []
    # record steel tiles
    for tile in player.level.mapr:
        if tile.type == player.level.TILE_STEEL:
            steel_tile.append(tile)

    for enemy in tanks.enemies:
        # When enemy and player are in the same horizontal lines
        # -17 15
        if -15 < player.rect.top - enemy.rect.top < 13 and enemy.state == enemy.STATE_ALIVE:
            for tile in steel_tile:
                if (enemy.rect.left <= tile.left <= player.rect.left or enemy.rect.left <= tanks.castle.rect.left <= player.rect.left)\
                        and -17 < player.rect.top - tile.top < 5:
                    isFire = False
                    break
            # do not shot castle
            if (enemy.rect.left <= tanks.castle.rect.left - 16 <= player.rect.left or enemy.rect.left >= tanks.castle.rect.left -16 >= player.rect.left)\
                    and player.rect.top > 23*16:
                isFire = False

            # player is on the right side of the enemy
            if isFire and player.rect.left > enemy.rect.left:
                player.direction = player.DIR_LEFT
                player.fire()
            # player is on the left side of the enemy
            if isFire and player.rect.left < enemy.rect.left:
                player.direction = player.DIR_RIGHT
                player.fire()

        # When enemy and player are in the same vertical lines
        if -15 < player.rect.left - enemy.rect.left < 13 and enemy.state == enemy.STATE_ALIVE:
            for tile in steel_tile:
                if (enemy.rect.top <= tile.top <= player.rect.top or enemy.rect.top >= tile.top >= player.rect.top)\
                        and -17 < player.rect.left - tile.left < 5:
                    isFire = False
                    break
            # player is below the enemy
            if isFire and player.rect.top > enemy.rect.top:
                player.direction = player.DIR_UP
                player.fire()
            # player is above the enemy
            elif isFire and player.rect.top < enemy.rect.top:
                player.direction = player.DIR_DOWN
                player.fire()


def autoEscape (player):
    # escape from bullets
    # 当player与子弹距离过近时，非常容易escape失败。猜测是两个条件都符合，导致player选择了错误的方向，或者无论选择什么方向都会中弹
    isEscape = True
    steel_tile = []
    # record steel tiles
    for tile in player.level.mapr:
        if tile.type == player.level.TILE_STEEL:
            steel_tile.append(tile)

    for bullet in tanks.bullets:
        if bullet.owner == bullet.OWNER_ENEMY:
            if -26 < player.rect.top - bullet.rect.top < 8 and (
                    bullet.direction == bullet.DIR_RIGHT or bullet.direction == bullet.DIR_LEFT):
                # if there's steel tile between bullet and player, no need to escape
                for tile in steel_tile:
                    if (bullet.rect.left <= tile.left <= player.rect.left or bullet.rect.left >= tile.left >= player.rect.left) \
                            and -17 < player.rect.top - tile.top < 5:
                        isEscape = False
                        break
                if isEscape and -9 < player.rect.top - bullet.rect.top < 8:
                    player.direction = player.DIR_DOWN
                elif isEscape and -26 < player.rect.top - bullet.rect.top <= -9:
                    player.direction = player.DIR_UP

            elif -26 < player.rect.left - bullet.rect.left < 8 and (
                    bullet.direction == bullet.DIR_UP or bullet.direction == bullet.DIR_DOWN):
                # if there's steel tile between bullet and player, no need to escape
                for tile in steel_tile:
                    if (bullet.rect.top <= tile.top <= player.rect.top or bullet.rect.top >= tile.top >= player.rect.top) \
                            and -17 < player.rect.left - tile.left < 5:
                        isEscape = False
                        break
                if isEscape and -9 < player.rect.left - bullet.rect.left < 8:
                    player.direction = player.DIR_RIGHT
                elif isEscape and  -26 < player.rect.left - bullet.rect.left <= -9:
                    player.direction = player.DIR_LEFT


def autoPlay(player, time_passed):
    """Contrl the players"""

    # if player meet enemy, fire
    autoFire(player)
    # escape from bullets
    autoEscape(player)
    # update position
    autoMove(player)

    # move to bonus
    # global chasingBonus
    # if len(tanks.bonuses) > 0 and not chasingBonus:
    #     chasingBonus = True
    #     moveToBonus(player, tanks.bonuses[0])
    # elif len(tanks.bonuses) == 0:
    #     autoMove(player)
    #     chasingBonus = False


def autoTest():
    # this is a bug from the original game, player do not have the timer_uuid_fire,
    # but when fire, tank need to destroy the timer_uuid_fire. Thus, add a test function to make up
    global start
    while start:
        pass

    time.sleep(3)
    for player in tanks.players:
        player.timer_uuid_fire = tanks.gtimer.add(1000, lambda: test())  # run just once

    # Start the main loop for the game
    mainLoop = True
    while mainLoop:
        while tanks.game.running and not tanks.game.game_over:
            time_passed = tanks.game.clock.tick(30)
            # tanks.game.level.buildFortress(tanks.game.level.TILE_STEEL)
            gameBugLog()
            player_index = 0
            for player in tanks.players:
                autoPlay(player, time_passed)    # record bugs
                playerBugLog(player, player_index)
                if len(tanks.players) == 2:
                    if player_index == 0:
                        player_index = 2
                    elif player_index == 2:
                        player_index = 0

        # if tanks.game.game_over:
        #     mainLoop = False


def drawScreen( nr_of_players):
    """draw the intro screen"""
    font = pygame.font.Font("fonts/prstart.ttf", 16)
    tanks.screen.fill([0, 0, 0])
    tanks.screen.blit(font.render("Battle City AutoTest", True, pygame.Color('white')), [100, 150])
    tanks.screen.blit(font.render("1 PLAYER", True, pygame.Color('white')), [165, 250])
    tanks.screen.blit(font.render("2 PLAYERS", True, pygame.Color('white')), [165, 275])
    normal_font = pygame.font.Font(None, 25)
    tanks.screen.blit(normal_font.render("Press Esc to check rules", True, pygame.Color('white')), [140, 340])
    sprites = pygame.transform.scale(pygame.image.load("images/sprites.gif"), [192, 224])
    player_image = pygame.transform.rotate(sprites.subsurface(0, 0, 13 * 2, 13 * 2), 270)

    if nr_of_players == 1:
        tanks.screen.blit(player_image, [125, 245])
    elif nr_of_players == 2:
        tanks.screen.blit(player_image, [125, 270])

    pygame.display.flip()


def drawRuleScreen ():
    """draw the rule screen"""
    font = pygame.font.Font(None, 40)
    tanks.screen.fill([0, 0, 0])
    tanks.screen.blit(font.render("The way to start", True, pygame.Color('white')), [130, 100])
    font = pygame.font.Font(None, 25)
    tanks.screen.blit(font.render("You can type the level you want to start, if you do", True, pygame.Color('white')), [40, 150])
    tanks.screen.blit(font.render("not enter or the text is not number or out of rage, ", True, pygame.Color('white')), [40, 170])
    tanks.screen.blit(font.render("it will default start with the first level. ", True, pygame.Color('white')), [40, 190])
    tanks.screen.blit(font.render("Then you can use PgUp and PgDown button to", True, pygame.Color('white')), [40, 220])
    tanks.screen.blit(font.render("choose 1 player mode or 2 player mode.", True, pygame.Color('white')), [40, 240])
    tanks.screen.blit(font.render("The default mode is 1 player mode.", True, pygame.Color('white')), [40, 260])
    tanks.screen.blit(font.render("After choosing, press Enter to start the game.", True, pygame.Color('white')), [40, 290])
    tanks.screen.blit(font.render("NOW PRESS ENTER TO RETURN.", True, pygame.Color('white')), [100, 330])
    # Then you can use PgUp and PgDown button to choose 1 player mode or 2 player mode. The default mode is 1 player mode.
    # After choosing, you can press Enter to start the game. 
    main_loop = True
    pygame.display.flip()
    while main_loop:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                main_loop = False
            elif event.type == KEYDOWN:
                if event.key == pygame.K_RETURN:
                    print ('here')
                    introScreen()
                    pygame.display.flip()
                    main_loop = False


def playerBugLog (player, player_index):
    """record player's bug"""
    currentTime = time.strftime('%Y-%m-%d %H:%M', time.localtime(time.time()))  # record current time
    # boundary check
    if player.rect.left < 0 or player.rect.left > 416 - 26:
        logging.debug(currentTime + player_index + ' level' + str(tanks.game.stage) + ':tank out of left or right boundary.')
    if player.rect.top < 0 or player.rect.top > 416 - 26:
        logging.debug(currentTime + player_index + ' level' + str(tanks.game.stage) + ':tank out of top or bottom boundary.')

    for bullet in tanks.bullets:
        # bullet and castle
        if bullet.rect.colliderect(player.rect) and bullet.owner == bullet.OWNER_ENEMY:
            logging.debug(currentTime + ' level'+ str(tanks.game.stage) + ':player' + str(player_index) + ' has been shot.')

    # check if tanks get stuck
    playerStuckCheck(player, player_index)


def gameBugLog ():
    """record bugs of enemies, bullets and other game elements"""

    # create record dir and files
    rq = time.strftime('%Y-%m-%d-%H', time.localtime(time.time()))
    log_path = os.getcwd() + '/Logs/all/'
    # log_path = os.getcwd() + '/../Logs/all/'
    log_name = log_path + rq + '_all.log'
    logfile = log_name
    currentTime = time.strftime('%Y-%m-%d %H:%M', time.localtime(time.time()))

    if not os.path.exists(log_path):
        os.makedirs(log_path)
    # create file if not exist
    if not os.path.exists(logfile):
        f = io.open(logfile, mode='w', encoding="utf-8")
        f.close()
    logging.basicConfig(filename=os.path.join(os.path.dirname(log_path), logfile), level=logging.DEBUG)

    # enemy stuck check
    enemyStuckCheck()

    # interaction check
    interactionCheck()

    # level finished
    if len(tanks.game.level.enemies_left) == 0 and len(tanks.enemies) == 0:
        logging.debug(currentTime + ' level' + str(tanks.game.stage) + ' completed')

    # check if player destroyed the castle
    for bullet in tanks.bullets:
        # bullet and castle
        if bullet.rect.colliderect(tanks.castle.rect) and bullet.owner == bullet.OWNER_PLAYER:
            logging.debug(currentTime + ' level'+ str(tanks.game.stage) + ':castle destroyed by player')

    if tanks.game.game_over:
        # record game over reason
        if not tanks.castle.active:
            global castleDestroyed
            castleDestroyed += 1
            logging.debug(currentTime + ' level' + str(tanks.game.stage) + ' gameOver: castle has been destroyed.' + 'Total destroyed ' + str(castleDestroyed) + ' times.' )
        # else:
        #     logging.debug(currentTime + ' level' + str(tanks.game.stage) + 'gameOver: player die')

        # restart the game
        global restart
        restart = True
        tanks.game.game_over = False
        tanks.game.running = False
        tanks.game.stage = tanks.game.stage - 1

        global playerXY, enemyXY, playerStuck, enemyStuck
        playerXY = [[0 for i in range(20)] for j in range(4)]
        enemyXY = [[0 for i in range(20)] for j in range(8)]
        playerStuck = [False] * 2
        enemyStuck = [False] * 4
        logging.debug(currentTime + ' level' + str(tanks.game.stage + 1)  + ':Restart the game.')

        time.sleep(3)


def interactionCheck():
    pass
    # TO BE DONE
    # tank and tile
    # bullet and tanks
    # bullet and enemy
    # for enemy in tanks.enemies:
    #     if enemy.rect.colliderect(bullet):
    #         if enemy.state == enemy.STATE_ALIVE and bullet.owner == bullet.OWNER_PLAYER:
    #             logging.debug(currentTime + ' level' + str(tanks.game.stage) + ':enemy self destroy failed')

    # when player's bullet shot tiles
    # has_collided = False
    # tile and bullet
    # rects = bullet.level.obstacle_rects
    # collisions = bullet.rect.collidelistall(rects)
    # if collisions != []:
    #     for i in collisions:
    #         if bullet.owner == bullet.OWNER_PLAYER and bullet.state == bullet.STATE_ACTIVE:
    #             logging.debug(currentTime + ' level' + str(tanks.game.stage) + ':remove tile failed')

    # if bullet.level.hitTile(rects[i].topleft, bullet.power, bullet.owner == bullet.OWNER_PLAYER):
    #     print ('bullet from player')
    #     has_collided = True
    # if bullet.state != bullet.STATE_REMOVED:
    #     logging.debug(rqm + ' level' + str(tanks.game.stage) + ' bullet did not explode')


def get_key():
    while 1:
        event = pygame.event.poll()
        if event.type == pygame.QUIT:
            return event.type
        if event.type == KEYDOWN:
            return event.key
        else:
            pass


def display_box(screen, message):
    "Print a message in a box in the middle of the screen"
    fontobject = pygame.font.Font(None,22)
    pygame.draw.rect(screen, (0,0,0),
                   ((screen.get_width() / 2) - 100,
                    (screen.get_height() / 2) - 10,
                    200, 30), 0)
    pygame.draw.rect(screen, (255,255,255),
                   ((screen.get_width() / 2) - 102,
                    (screen.get_height() / 2) - 12,
                    210,24), 1)
    if len(message) != 0:
        screen.blit(fontobject.render(message, 1, (255,255,255)),
                ((screen.get_width() / 2) - 100, (screen.get_height() / 2) - 10))
    pygame.display.flip()


def introScreen ():
    """create game variables and update the intro screen"""
    tanks.game = tanks.Game()
    tanks.castle = tanks.Castle()
    tanks.game.stage = 0
    tanks.game.nr_of_players = 1
    drawScreen(tanks.game.nr_of_players)

    # create level input box
    pygame.font.init()
    current_string = []
    # display_box(tanks.screen, "Level (1 to 35):" + string.join(current_string, ""))
    display_box(tanks.screen, "Level (1 to 35):" + "".join(current_string))

    # start the main loop of choosing player mode and level
    main_loop = True
    while main_loop:
        time_passed = tanks.game.clock.tick(50)

        inkey = get_key()
        if inkey == pygame.QUIT:
            main_loop = False
            global quitGame
            quitGame = True
            pygame.quit()
            sys.exit()

        elif inkey == K_BACKSPACE:
            current_string = current_string[0:-1]
        elif inkey == K_RETURN:
            main_loop = False
        elif inkey == K_MINUS:
            current_string.append("_")

        elif inkey == K_UP:
            if tanks.game.nr_of_players == 2:
                tanks.game.nr_of_players = 1
                drawScreen(tanks.game.nr_of_players)
        elif inkey == pygame.K_DOWN:
            if tanks.game.nr_of_players == 1:
                tanks.game.nr_of_players = 2
                drawScreen(tanks.game.nr_of_players)
        elif inkey == pygame.K_ESCAPE:
            drawRuleScreen()
            main_loop = False
        elif inkey <= 127:
            current_string.append(chr(inkey))
        display_box(tanks.screen, "Level (1 to 35):" + "".join(current_string))

    # pygame.display.flip()

    # update level input box
    level = "".join(current_string)
    if level != '' and level.isdigit():
        tanks.game.stage = int(level) - 1
    global start
    start = False


def runGame():
    # enter the game
    currentTime = time.strftime('%Y-%m-%d %H:%M', time.localtime(time.time()))
    logging.debug(currentTime + ':Start from level ' + str(tanks.game.stage))
    tanks.game.nextLevel()


def playerStuckCheck(player, player_index):
    # player stuck check
    global playerXY, playerStuck
    rqm = time.strftime('%Y-%m-%d %H:%M', time.localtime(time.time()))  # record current time
    second = int(time.strftime("%S", time.localtime()))
    if second % 3 == 0:
        index = second / 3 - 1
        playerXY[player_index][index] = player.rect.left
        playerXY[player_index + 1][index] = player.rect.top
        if 1 < index < 20 and not tanks.game.timefreeze:
            if abs(playerXY[player_index][index] - playerXY[player_index][index - 1]) < 2\
            and abs(playerXY[player_index + 1][index] - playerXY[player_index + 1][index - 1]) < 2\
            and abs(playerXY[player_index][index - 1] - playerXY[player_index][index - 2]) < 2\
            and abs(playerXY[player_index + 1][index - 1] - playerXY[player_index + 1][index - 2]) < 2 and not playerStuck [player_index / 2]:
                playerStuck[player_index / 2] = True
                # print ('player tank get stuck')
                logging.debug(rqm + 'player tank get stuck')


def enemyStuckCheck():
    # enemy stuck check
    global enemyXY
    index_enemy = 0
    currentTime = time.strftime('%Y-%m-%d %H:%M', time.localtime(time.time()))  # record current time
    second = int(time.strftime("%S", time.localtime()))
    if second % 3 == 0 and index_enemy < 8:
        for enemy in tanks.enemies:
            index = second / 3 - 1
            enemyXY[index_enemy][index] = enemy.rect.left
            enemyXY[index_enemy + 1][index] = enemy.rect.top

            if 1 < index < 20 and not tanks.game.timefreeze:  # in case index out of range
                if abs(enemyXY[index_enemy][index] - enemyXY[index_enemy][index - 1]) < 2 and abs(
                        enemyXY[index_enemy + 1][index] - enemyXY[index_enemy + 1][index - 1]) < 2 and abs(
                    enemyXY[index_enemy][index - 1] - enemyXY[index_enemy][index - 2]) < 2 and abs(
                    enemyXY[index_enemy + 1][index - 1] - enemyXY[index_enemy + 1][index - 2]) < 2 and not enemyStuck[index_enemy / 2]:
                    enemyStuck[index_enemy / 2] = True
                    # print ('enemy tank get stuck')
                    logging.debug(currentTime + 'enemy tank get stuck')
            index_enemy = index_enemy + 2


# TO BE DONE
def moveToBonus (player, bonus):
    # dest = pygame.Rect(200, 240, 26, 26)
    print ('once')
    dest = bonus.rect
    # 根据top大小选择网上或往下
    if dest.top < player.rect.top and abs(player.rect.top - dest.top) > 2 and player.direction != player.DIR_UP:
        player.direction = player.DIR_UP
        # player.fire()
    elif dest.top > player.rect.top and abs(player.rect.top - dest.top) > 2 and player.direction != player.DIR_DOWN:
        player.direction = player.DIR_DOWN
        # player.fire()
    global chasingBonus
    while chasingBonus:
        if abs(player.rect.top - dest.top) < 2 < abs(player.rect.left - dest.left):
            # print player.rect
            if dest.left < player.rect.left and player.direction != player.DIR_LEFT:
                player.direction = player.DIR_LEFT
                # player.fire()
            elif dest.left > player.rect.left and player.direction != player.DIR_RIGHT:
                player.direction = player.DIR_RIGHT
                # player.fire()

    if player.direction == player.DIR_UP:
        new_position = [player.rect.left, player.rect.top - player.speed]
        if new_position[1] < 0:
            turnAround(player)
            return

    elif player.direction == player.DIR_RIGHT:
        new_position = [player.rect.left + player.speed, player.rect.top]
        if new_position[0] > (416 - 26):
            turnAround(player)
            return

    elif player.direction == player.DIR_DOWN:
        new_position = [player.rect.left, player.rect.top + player.speed]
        if new_position[1] > (416 - 26):
            turnAround(player)
            return

    elif player.direction == player.DIR_LEFT:
        new_position = [player.rect.left - player.speed, player.rect.top]
        if new_position[0] < 0:
            turnAround(player)
            return
    player_rect = pygame.Rect(new_position, [26, 26])

    # collisions with tiles
    if player_rect.collidelist(player.level.obstacle_rects) != -1:
        player.fire()
        if player.direction == player.DIR_UP or player.direction == player.DIR_DOWN:
            if dest.left > player.rect.left:
                player.direction = player.DIR_RIGHT
            else:
                player.direction = player.DIR_LEFT
        elif player.direction == player.DIR_LEFT or player.direction == player.DIR_RIGHT:
            if dest.top > player.rect.top:
                player.direction = player.DIR_DOWN
            else:
                player.direction = player.DIR_UP
        return

    # collisions with other players
    for pl in tanks.players:
        if pl != player and pl.state == pl.STATE_ALIVE and player_rect.colliderect(pl.rect):
            turnAround(player)
            return

    # collisions with enemies
    for enemy in tanks.enemies:
        if player_rect.colliderect(enemy.rect):
            turnAround(player)
            return

    # collisions with bonuses
    for bonus in tanks.bonuses:
        if player_rect.colliderect(bonus.rect):
            player.bonus = bonus

    player.rotate(player.direction)
    player.rect.topleft = (new_position[0], new_position[1])


def varInitiate():
    # create game variables since the intro screen need to use the screen created by original game
    tanks.gtimer = tanks.Timer()
    tanks.sprites = None
    tanks.screen = None
    tanks.players = []
    tanks.enemies = []
    tanks.bullets = []
    tanks.bonuses = []
    tanks.labels = []
    tanks.play_sounds = False
    tanks.sounds = {}
    tanks.game = None
    tanks.castle = None
    # tanks.castle = tanks.Castle()
    # tanks.game = tanks.Game()
    # tanks.game.stage = 0
    # tanks.game.nr_of_players = 1


if __name__ == '__main__':

    # global variables for tanks stuck check
    playerXY = [[0 for i in range(20)] for j in range(4)]
    enemyXY = [[0 for i in range(20)] for j in range(8)]
    playerStuck = [False] * 2
    enemyStuck = [False] * 4
    chasingBonus = False
    start = True
    restart = True
    quitGame = False
    castleDestroyed = 0
    # playerDie = 0
    varInitiate()

    # multithread to start game and auto test
    y = threading.Thread(target=autoTest)
    y.start()

    introScreen()
    while start:
        pass
    while True:
        while not restart:
            pass
        else:
            restart = False
            time.sleep(0.01)
            runGame()



