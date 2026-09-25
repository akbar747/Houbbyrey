#1.导入工具包
import pygame      #专门用来做游戏的工具箱
import sys         #用来关闭程序的工具箱
import random      #用来形成随机数的工具箱（随机生成食物）

#2.初始化设置
pygame.init()      

#3.设置游戏窗口
screen = pygame.display.set_mode((400,400))          #创建黑色布块高400，宽400
pygame.display.set_caption("贪吃蛇")                 #窗口起标题

#4.游戏数据（记录贪吃蛇的状态）
snake_body = [(100,100)]     #蛇的身体坐标列，一开始有一节，在（100，100）的位置
dx = 1                       #水平方向速度：1代表向右，-1代表向左，0代表不动
dy = 0                       #垂直方向速度：1代表向右，-1代表向左，0代表不动
speed = 20                 #每次移到的像素距离（也就是方块的边长）

#5.食物数据（随机生成食物的坐标）
food_x = random.randrange(0,400,20)     #在0到400之间随机找位置，步长为20（对齐格子）
food_y = random.randrange(0,400,20)     #同上，y轴

#6. 游戏时长
clock = pygame.time.Clock()      #创建一个时钟对象
move_timer = 0                   #计时器，用来记录
move_delay = 300                 #延迟时间（毫秒）

#7.游戏主循环（游戏的心脏，无限循环，不断刷新画面）
running = True                  #控制游戏是否继续运行的开关
while running:
    dt = clock.tick(60)         #规定游戏毫秒最多循环60次，并记录每次循环花费多少毫秒

#8.玩家处理的操作（听指令）
    for event in pygame.event.get():   #把玩家所以的操作（键盘，鼠标）都拿出来看一编
        if event.type == pygame.QUIT:  #如果玩家点了窗口右上角的“X”
            runing = False             #把开关关掉，游戏结束

        if event.type == pygame.KEYDOWN:                   #如果玩家点了键盘
            if event.key == pygame.K_LEFT and dx == 0:     #按左键，且当前不存在左右运动时
                dx = -1                                    #改为向左
                dy = 0
            if event.key == pygame.K_RIGHT and dx == 0:    #按右键
                dx = 1                                     #改为向右
                dy = 0
            if event.key == pygame.K_UP and dy == 0:       #按上键
                dx = 0
                dy = -1                                   #改为向上
            if event.key == pygame.K_DOWN and dy == 0:    #按下键
                dx = 0
                dy = 1                                    #改为向下

#9.计算移动（蛇怎么走）
    move_timer += dt                     #累加时间
    if move_timer >= move_delay:         #如果累加的时间超过了设定的延迟（比如300毫秒）
        move_timer = 0                   #计算器清零，准备下一轮

        last_x, last_y = snake_body[-1]                        #找到蛇头（列表里最后一个元素）的坐标
        new_head = (last_x + dx * speed,last_y + dy *speed)    #计算新蛇头要去的位置

#10.撞墙检测
        if new_head[0] < 0 or new_head[0] > 380 or new_head[1] < 0 or new_head[1] > 380:
            print("碰墙了!游戏结束！")         #会在底部输出这一行字
            funning = False                    #游戏结束
        else:
            snake_body.append(new_head)        #把新头加到蛇的身体里

#11.吃食物检测
            if new_head[0] == food_x and new_head[1] == food_y:  #如果蛇头的位置和食物重合
                print("吃到食物了！")                            #会底部输出这一行字
                food_x = random.randrange(0,400,20)              
                food_y = random.randrange(0,400,20)              #重新生成的食物位置
                                                                 #注意;这里没删掉蛇尾巴，所以蛇边长
            else:
                snake_body.pop(0)                                #如果没有吃到食物，就把最久的尾巴删掉，保持长度不变

#12.绘制画面
    screen.fill((255,255,255))                                   #先用白色把上一帧的画面盖住（撒黑板）                    


    pygame.draw.rect(screen,(0,255,0),(food_x,food_y,20,20))     #画绿色的食物


    for segment in snake_body:                                   #遍历蛇身体的每一节
        pygame.draw.rect(screen,(255,255,0),(segment[0],segment[1],20,20))     #画黄色的蛇


    pygame.display.flip()                                        #把刚才画好的东西，一次性显示到屏幕

#13.退出游戏
pygame.quit()                                                    
sys.exit()
