# 备战第十八届智能视觉

## 2022/11/30  

备战第十八届智能车，参加智能视觉组，**以此来记录此次比赛经历和过程，为以后的自己提供相应的参考**

 1. 首先该做的事情是将硬件和底层做出来，在算法实现的基础上确定好大致框架，例如RT1064最小系统版的学习和RT-Thread操作系统的学习，确定好中央处理器模块的框架，然后再进行PCB板子的打板，焊接和测试，最后进行相应的图像识别，路径规划等相应的算法。  

 2. 2022年即将结束，2022造神计划实现的不尽人意，但终是还是有一定的收获，这一年给我的启示就一句话：坚持，保持热爱，持之以恒的去做某一件事。接下来的生活中，再一次提醒自己坚持去做，比如背英语，健身。

## 2023/1/16

 RT-Thread操作系统大致学习完毕，大多数驱动和设备都调试完成，接下来准备制作第一项功能-----使用蓝牙串口来控制小车运动

## 2013/1/19

蓝牙串口来控制小车运动基本实现，发现一个巨大问题，在运动中平移或者转向误差很大，需要一些pid等控制来减小误差，我发现光靠自己想会浪费很多时间，多看看报告和论文资料，来快速解决问题。RTThread操作系统还是比较难以上手。

### PID 在做车中的应用  

首先，电机的控制是通过编码器返回的实时速度与期望速度进行 PID 的调节从而实现速度上的闭环，从而实现小车的速度与我期望的速度实现真正的相同。这里我们采用了增量式 PID 进行调节，当小车比期望速度慢时，通过计算给出一个比较大的占空比，使电机加速旋转，当小车比期望速度快时，通过计算输出一个小的占空比，使电机减速，从而实现速度上的跟随。  
其次，车位矫正通过在图像中寻找到目标图片中心和我们设定的适合车进行拾取的点做 x 轴和 y 轴上两个方向的偏差，当偏差比较大时，我认为此时距离图片比较远，需要大一点的速度进行调整，当偏差较小时，我认为此时离目标图片比较近，这个时候不需要太大的速度，避免超调。在跑到目标点的过程中，这个时候车只需要给一个固定速度跑就行，因为这个时候车跑的是直线。除此之外，我们改变原有的单环控制算法，使用串级 PID 的控制思路在多个控制中，对智能车的性能指标有了显著的提升，在 M 车的控制中，引入角速度环，抗干扰效果好，再将角度环串在角速度环上，最后速度环叠加在角度环上，方向环上也是同样的方法，在方向环的控制中，会出现大量的跳变输出，对此需要对按照需要对 pid 的输出做一个递推滤波，保证输出的平稳。  
需要注意的是，串级 pid 控制中，需要先整定内环参数，内环精调，外环粗调，可以先将外环给一个固定值，整定内环参数，当调整好之后，再整定外环，每一级的输出再限幅，可以使控制精确快速不超调，并且每一级之间控制周期需要大于至少 2 倍。在方向环的控制中，使用动态 p，使 p 的大小呈二次函数关系，并乘以速度系数，对输出做限幅，经过测试，可以很快速通过图片对车身进行调整。

### 屏幕的多级显示，更直观方便调参和显示数据

通过一个结构体来进行屏幕多级的切换，方便了显示数据，但是如何调参还需要进一步优化

```c
typedef struct
{
  uint8 current; //当前状态索引号
  uint8 next;   //向下一个
  uint8 enter;  //确定
  uint8 back;   //退出
  void (*current_operation)(void); //当前状态应该执行的操作
} Menu_table;
```

**问题1**：编码值和pwm占空比和实际距离如何对应？
通过一个增量式pid，输入目标编码器值和当前编码器值，计算出占空比就可以了，不需要单独计算，编码器值可以对应实际距离

**问题2**：麦克纳姆轮如何解算x,y轴上的距离？

## 2023/2/7

加入了转向环，基本完成麦克纳姆轮的逆解算和正解算，加入了里程计和陀螺仪，可以进行下一步坐标的计算  

识别A4纸上的坐标（总钻风识别代码过于麻烦，先使用openart识别坐标）
图像如何进行预处理？  
1.大津法二值化

如何提取坐标，并且与实际对应？

1.搜索矩形，提取矩形长度和宽度  
①r.x() #获取矩形的左上角x像素坐标  
②r.y() #获取矩形的左上角y像素坐标  
③r.w() #获取矩形的宽度  
④r.h() #获取矩形的高度  

2.搜索圆点  
确定完矩形后，需要在矩形中找到所有的圆点，这时候就要用到find_circles函数，为了方便观察，同样使用draw_circle将搜索到的圆画到图像上。  
使用find_circles时需要设置一些参数：  
①roi = r.rect() #设置圆点搜索区域，这里设置为之前确定的矩形  
②threshold = 1800 #和搜索矩形中参数相同，值越小，越容易搜索圆形特征  
③r_min = 1 #设置搜索圆的最小半径  
④r_max = 5 #设置搜索圆的最大半径  
⑤r_step = 1 #设置搜索圆的步长（每移动多少像素检测一次圆）  
设置完成后运行，在图像上便能看到矩形和圆点已经被正确的标识到。  

搜索到圆形后，一般用到三个方法来获取圆形的数据  
①c.x() #获取圆形的x像素坐标  
②c.y() #获取圆形的y像素坐标  
③c.r() #获取圆形的半径  
当然，现在的坐标还只是像素坐标，还需要按照等比的方式计算为真实坐标。  
在OpenART mini中，图像的左上角为（0，0），从上向下，Y轴增加，从左向右，X轴增加，单位为像素。  

在X轴方向上的计算为（圆点X像素坐标–矩形X像素坐标）/ 矩形的宽度得到圆点在X轴上的比例，再乘上实际最大坐标35，便能得到以0为基点的X坐标，再加上1得到真实的X坐标。

在Y轴方向上的计算为（圆点Y像素坐标–矩形Y像素坐标）/ 矩形的高度得到圆点在Y轴上的比例，再乘上实际最大坐标25，因为Y轴和实际是相反的，所以还需要用25减去计算的值便能得到到以0为基点的Y坐标，再加上1得到真实的Y坐标。

## 2023/2/9

  已经实现openart识别坐标点并与单片机形成通讯，接下来如何使用这些坐标点，并跑到相应的位置还需要考虑和解决

1. 如何进行路径规划？  
2. 如何让小车进行规划后的移动？  
3. 如何进行姿态矫正？  

为了纠正由于陀螺仪和编码器积分导致的误差，车模在到达图片附近后再进行一定的矫正。矫正的误差有偏移距离误差和角度误差。图像经过二值化后，把图片的边缘凸显出来，计算出图片行列位置的重心，通过 pid 控制使重心到达理想位置。然后遍历图像，找到图片的上顶点和左右顶点，计算出角度，从而纠正车模的姿态。

OPENART连接TFT显示屏需要一个PCB转接板  
  已通过用IPS114形成显示，但是好像无法同时和串口功能同时使用？

如何减小陀螺仪的误差？

1. 零点漂移
2. 陀螺仪的误差分析（系统性误差和随机误差）
3. 加速度计数据和速度数据的滤波（减少震动）→对速度进行相应的滤波
4. 温漂  

加速度包括重力加速度，陀螺仪测量的是角速度，需要通过积分成等其他手段来获取角度。

## 2023/3/26

已经初步完成小车跑点运动，具体性能和转向方式有待提升  

接下来完成识别卡片并和小车实现通讯，同时也能够进行位姿调节，做到跑到点位然后实现检测的功能  

下一步,矫正和识别通讯都完成之后，进行搬运并且优化路径规划

完成以上功能后，已经完成70%，可以完成上一届比赛之后，开始进行对于目标检测的功能实现

## 2023/4/3

由于没有场地，绝大多数无法进行良好的测试，还有需要制做和调整的部分比较多，接下来这些部分就是之后所需要的主要目标：

1. 板子的焊接
虽然板子画了好了，但是在焊接过程上出现了部分问题，无法将板子完整的焊接并且进行相应的测试，具体板子性能还未知，再加上机械部分还未想好如何实现具体流程导致无法修改和改良板子的性能。

2. 部分参数的调节
对于增量式pid， 位置式pid，角度环pid的调节只是粗调，能用，但是具体性能还未测试，这些是亟待提升和优化的。同时对于摄像头来说，均匀的光线是非常重要，对于光线的调节也需要测试。

3. 识别的准确率
识别的准确率是比赛的绝对关键，但是由于光线不均匀，场地颜色不均，模型准确率较差，数据集较少等等原因导致准确率无法达到令人满意的程度，所以这个地方也有待提升。

4. 部分算法的优化和调节
对于比赛流程来说，如何实现并符合规则上的搬运也需要思考，同时动态路径规划有没有必要写，怎么优化也需要考虑。同时对于目标检测如何对应的实际的坐标图中也需要思考和编写。同时，如果里程计和陀螺仪在实际运用中如果误差过大。如何优化也是个大问题，是否选择其他的运动方式也需要考虑。同时如果实在是无法正确识别目标。那么应该如何舍弃或者跳过该目标寻找下一个目标也需要考虑。

5. 机械部分
对于上述的目标检测和图像识别都需要一个合适的高度和角度，这个如何调节也需要大量测试寻找最优值，同时也要和算法部分一一对应。同时如何搬运，使用几个维度的机械臂，如何将卡片放置到小车上，或者使用仓之类的来存放也需要再思考，并且这个也要和算法部分一一对应

在场地找到之前，可以提升的如下：

1. 板子的绘制和焊接，测试和提升
2. 图像识别准确度的提升，图片数据的增广，训练时的参数调节等
3. 对于动态路径算法的编写，可以先使用这种算法来跑，如果有更好解可以后期再修改

## 2023/4/4

今天焊了半天板子，需要改进的部分有：

1. 部分元器件的布局，有些地方过于拥挤导致焊接比较困难，容易出现虚焊的问题
2. 在姿态传感器上需要加两个螺丝来固定，放置因为运动而导致的抖动
3. 部分元器件是否还需要？部分功能布局还需改动

**主板问题**:cr引脚上电不知道是不是有问题导致下部分3v3电源无法供电，舵机电源可能也有点问题，只有2.3v但是又偶尔和电池电压一样，其余问题暂时没有发现

**驱动板问题**:右边电机正转电压正常，反转电压接近0，好像是芯片问题，暂时没有找到具体问题所在
左半部分电机正转也正常，但是切换到反转之后好像是场效应管冒烟，然后有吱吱的响声，电压正常，但是再接正转电压只会慢慢上升

## 2023/4/10

目前的问题：

1. 矫正的问题，矫正的时候由于帧率较低，而且很容易判断错误，容易照到小车的前面，所以在这一块机械结构和算法上面都得优化，然后是否需要找到角点来调节小车位姿也是一个需要考虑的问题。  

2. 场地的问题，因为没有场地，所以在测试车上无法得到良好的反馈，比如说如何确定小车当前坐标和是否跑到相应的点位，而且蓝色背景布挺重要的，可以减少外界的干扰部分，所以场地对于后期的调试非常重要

3. 板子问题，板子已经是第二版，马上就能到货，到时候在学长的帮助下将板子及时焊好，用加热台热风枪等等一定要放置虚焊等等问题，这个是未来一个星期必须完成的任务

4. 移动模式问题，现在暂定的是让小车直接平移到目标点位，但是由于场地的问题无法得到反馈，但是通过查看别的大佬去年的视频，大部分是选择先转向然后前进的行径模式，所以这个部分还值得优化。

5. 路径优化问题，路径优化这个问题已经提出很久了但是依然没有得到及时的编写，这个属实是不应该 应该及时将提出的问题解决，而不是一直拖延下去，这个是绝对需要修改的地方
 目前暂定的路径优化就是将坐标排列好之后，分别跑到相应的位置，并且搬运到相应的位置。
    后期路径规划应该是动态路径规划，先从最近的点开始，搬运到相应位置，然后这个时候通过计算得出下一个最近的点，然后重复此过程并且搬运到指定地方。

## 2023/4/29

根据逐飞的方案，重新制定和规划方案和目标  

初步思路如下：

1. 使用编码器和陀螺仪的数据记录，完成车模的全局定位，可以实时得到车模的当前位置以及当前角度；
2. 对于有坐标点的目标，使用OpenART mini识别坐标，并将坐标信息发送到RT1064；
3. 利用全局定位移动到目标位置附近，使用总钻风矫正车模位置，确保车模移动到图片正方向；
4. 使用OpenART mini识别图片内容，根据内容进行分类搬运；
5. 搬运也是基于全局定位实现，搬运过程中如果识别到四周的黄色边框，进行车模的位置和角度矫正；
6. 循环第3到5步，直到有框图片全部搬运完成；
7. 对于没有坐标点的图片目标板，可以基于目标检测技术，使用纯遍历或者语音识别控制车模移动到无框图片，并完成识别和搬运；
8. 所有图片搬运完成，返回车库；
里面的关键点有：全局定位、OpenART识别处理、总钻风矫正处理、OpenART目标检测、语音控制。  

### 全局定位，运动函数接口，位置控制函数接口

全局定位放在定时器中断中运行，并实时更新自己的当前位置，不需要到达位置后手动更新  

1. 在有目标坐标时，车模会自动移动到目标位置，如果没有目标坐标时，可以任意控制车模的移动姿态，方便矫正车身。  
对这部分的要求如下：
2. 我可以使用函数统一控制车模的移动姿态，参数有移动速度，移动方向，自身旋转方向（后面统称为移动接口函数）。  
3. 控制过程中，调整车模的旋转方向，但整体移动方向不能收到影响。比如我设置车模的旋转角度为0度，往0度方向移动，中途我修改自身旋转角度为30度，车模的整体方向还是往0度移动而不能有角度偏移。  
4. 生成一张和场地一样等比例缩略全局地图，并显示车模在场地上的位置，车模的任意移动都实时更新到地图上。  
5. 再封装一个位置控制函数，参数为目标坐标，这个函数会计算自身的实时坐标与目标坐标的相对角度，自动调用移动控制接口移动过去
6. 识别A4纸：优化的方案是在识别到外接矩形后，使用r.corners()函数对内部矩形的角点进行搜索，然后使用img1.rotation_corr()矫正内部矩形（也就是A4纸），使用矫正后的图像识别坐标信息，最后显示到图像的左上角，效果如下图所示。可以看到在A4纸倾斜的情况下也有较好的效果。已经完成
7. 识别图像：调用色块识别函数，使用阈值，即可准确的找到目标图片。已经完成
8. 总钻风矫正图片（能用openart来矫正？）已经完成，
但是如果角度很正，角点则会乱识别，可能需要改进，如何通过一个数据包来发送所有矫正数据也需要完成
9. 目标检测和语音控制：**暂无想法**  

### 车模控制  

1. 出库
2. 路径规划（单搬运）
3. 校准位置（图片或者边界赛道）已完成矫正和边界矫正基本程序，如何和单片机通讯，控制效果需要提升
4. 搬运模式
5. 检测无框卡片

## 2023/5/19

矫正部分识别中心点和角度基本上完成，但是存在一下问题：

   1. 矫正**速度**较慢
   2. 矫正**准确度**较慢  

可能原因：  

   1. 每个电机的机械问题导致转速无法上来，可以给每个轮子进行单独的闭环控制，这样的话可能需要四个增量式pid来单独控制电机，工作量有点大  
   2. 矫正使用了一个位置pid，来计算摄像头中心和卡片的距离来控制电机移动，但是还是速度和准确度比较慢，急需优化  

其他的问题：

1. 训练集的训练问题：准确度较低，训练速度慢，需要多多训练和调试
2. 搬运结构：是否需要多搬？机械臂如何控制？路径如何规划？

最近的想法：  

  >大二寒假 参加智能车——智能视觉比赛 正在学习的知识：RT-Thread操作系统，RT1064单片机，图像处理，机器人的运动学，机器学习，主板的绘制和焊接，建立好小车的底层驱动，例如麦克纳姆轮的驱动，识别相应的卡片，自身位姿的调节。需要学习的算法PID控制，卡尔曼滤波算法，和图像处理算法（opencv）等。  

1. 回顾了一下自己的经历，很是感慨，发现自己从选择开始做车开始，已经学习了很多知识，成长了很多，但是逐渐发现学习这件事只会让人越来越不懂，同时需要学习的东西越来越多，我只能说还有巨大成长空间。  
2. 最近学习了一下四元数和卡尔曼滤波，我觉得可以尝试做一下imu和里程计的融合，同时如果学的比较好并且有时间的话，可以试着写一篇基于四元数通过互补卡尔曼滤波和拓展卡尔曼滤波来进行imu和里程计的融合论文，来提升一下自己的论文水平
3. 以上皆为想法，无论任何想法有需要有人去学习，去实践来验证，来证明想法的准确性，**纸上得来终觉浅，绝知此事要躬行**。

## 2023/5/27

已经完成的任务：

1. 转向环PD和电机闭环控制各个参数已经调节比较优良
2. 驱动板的焊接已经全部搞定，测试也是好使的，其余的符合比赛指标（是否需要多备几块防止出现其他问题？）

还需要改进的地方：

1. 矫正部分不够丝滑，而且串口发送的数据可能有噪声，需不需要进行滤波处理？
2. 图片识别正确率很低，试一试降低图片数量，减少重复的图片
3. 目标检测还没有做，这个可以先做一做
4. 机械臂的安装和购买
5. 主板的焊接
6. 部分程序的优化和编写，比如说如何实现车头朝一个位置进行平移，如何实现动态路径规划，如何实现和目标位姿的矫正和场地位姿的矫正

部分心得：  
有时候还是过于羡慕和向往一些美好的事情，并且总是为此和现实郁郁不乐，陷入内耗，从而降低学习效率，还郁郁不得志。  
其实不如把心思放简单一点，活在当下，享受现在的每一刻，不要有太多的攀比和嫉妒之心，简单而纯粹。

![图片](https://github.com/JinHeMu/smart-car/blob/main/pic1.jpg)

## 2023/5/30

重新写了部分驱动代码，马上六月份需要提速了，毕竟马上要比赛了，需要理一下思路，理一下代码，为后面的工作做一下铺垫  

1. 小车启动，初始化
2. 向OPENART1发送数据，来识别A4纸，接受到A4纸后发送接收到A4纸信号量
3. 接受A4纸信号量后，静态计算路径，找到最近点并运动到其点位，发送矫正信号量
4. 接受矫正信号量后，向OPENART1发送数据，来矫正位姿，矫正完毕后，发送识别信号量
5. 接受识别信号量后，向OPENART1发送数据，来识别卡片，识别卡片后，选择搬运的位置，并运动到目标位置
6. 到达目标位置之后，运动到下一个坐标点位置，并循环4 ~ 5
7. 当所有目标位置都到达后，释放目标检测信号量
8. 接受目标检测信号量，开始遍历所有场地，直到接收到OPENART2发送的数据，记录当前位置，并重复4 ~ 5
9. 当遍历所有场地后，发送回库信号量，接受回库信号量后，返回车库。

大致流程如上，具体细节有待优化。  

## 2023/6/6

修改了部分运动函数，加入了舵机驱动和目标检测功能，商讨了机械结构，还需要改进的地方

1. 由于车会踢到卡片，导致车身会歪，此时再平移移动就会出现问题，所以需要优化一下运动函数
2. 机械机构决定了搬运算法和硬件，所以及时确定好机械结构，才能往下编写控制算法和硬件设计
3. 目标检测没有实机演示，只是初步尝试，需要多次尝试来确定如何优化
4. 矫正完成后，可能会出现小车搬运的时候仍然在运动的情况，而且可能会偏离中心位置
5. 速度快的时候到达某一个点位会出现大幅的偏移，这个需要再解决

## 2023/6/7

重大突破，由于识别卡片的时候，给模型输入的是整张图片，而不是小的那一小块图片，所以就会产生靠近的时候反而识别的更准确，
是由于img.copy()导致的，没有给图片进行一定的裁剪复制处理。

比较大的问题：当运动比较远的地方的时候，会出现停止不下来的问题，目前所观察到的问题可能是增量式pid的问题，由于运动时间过长，
对于误差的积分过大，到达的时候会出现大量的超调，就会停不下来，目前的解决措施可能是给误差的积分进行限幅处理，防止过大。

## 2023/6/11

对于上次的问题，给增量式PID加入了一个**限幅**处理，非常有效的解决的积分饱和问题，增强了系统的响应能力，同时也完善了各个功能之间的通讯模式，现在基本上已经实现，搬运，识别等功能，但是还是不够很完美，所以接下来应该主要以优化以下的功能为主  

1. **目标检测问题**，已经初步实现目标检测功能，但是不知道模型准确度够不够，然后如何移动到目标位置，如何转向相应的位置，也是需要解决的问题
2. **里程计问题**，发现小车到达目标点的时候，会有一定的误差，先减小运动函数到达的误差试一试，如果效果不够好的话，就试一试大佬们那种转到目标角度然后再直线运动的运动模式
3. **识别问题**，现在识别的也不够精准，这个具体思路不太多，可能还是要多次eiq训练出效果比较好的模型
4. **机械结构和硬件问题**，李乐乐学长做的模型，等到安装后不知道具体效果如何，同时又使用了很多的舵机和电磁铁，不知道电路板的效率和供电能不能跟得上，电流会不会太大导致电源问题。同时还需要优化一下搬运的算法
5. **边线矫正问题**，还未进行调试
6. **矫正问题**，卡片矫正时，可能会带动小车转动，此时再平移移动就会出现以小车坐标而不是世界坐标来进行移动，这个可能需要改进，或者是转向之后再转回来，这个需要一定的考虑。同时矫正过程中会稍稍偏移一些，可以降低速度或者是用其他的方法来优化，这个也是一个比较小的问题

暂且能想到的问题大概这么多，还需要及时的进行调试和优化，只能说今天是很有希望的一天，至少不是像之前那样束手无策，看不到完赛的一丝影子。

## 2023/6/15

机械结构绝大部分已经安装完毕，由于重量的增加，不知道一些参数是否需要一定的修改，板子到之后焊接就应该是完全体了，为了以防万一，可能需要多焊几块驱动板和主板来以防万一。  
在驱动板到之前，可以先调试一下机械臂，同时考虑仓旋转的角度，这些都可以调试出来。  
同时如何完成规则的任务，如何搬运，如何进行路径规划也是亟待解决的问题，由于最近可能考试有点多，所以必须要提高效率，毕竟现在留下的时间并不是很多，多动手多实践，少陷入虚无主义之中，毕竟这一个月的目标应该是很清楚的：**完成比赛,尽量不挂科**。

## 2023/6/22

今天将机械机构基本上安装完毕，机械臂和仓测试完毕  
今天最大的问题就是在锯杆子的时候，**自以为是并且还嫌弃麻烦**导致的电池也被割了一下，有个小口，并且已经漏液无法使用，经济损失是最直接的，如果没有及时发现，那将是一个重大的安全隐患，所以这个问题非常巨大，必须要提高警惕，避免这种行为再次发生。  
稍微跑了一下车，发现车已经跑不动了，初次判断应该是安装了机械臂和仓，导致重量增加，之前的参数已经现在不好使了，所以这些参数需要在明天将其调好（先使用他们的电池来判断是否是电池的问题？）  
**识别准确度还是很低**

## 2023/6/26  

调了一个端午假期和星期日，总体发现问题还是很多，没有像视频大佬车那么丝滑，总体来说可能还是电机控制和角度环控制的问题，会有抽搐的现象。同时启动速度过大也会导致车身抖动，漂移，所以电机控制和转向控制还需要再优化优化。  
加入了目标检测和回库的功能，不过在什么时候进行边线检测有待考虑，两个功能还需要再测试测试。

## 2023/6/30

基本上实现了除了目标检测以外的功能，速度也可以，但是还是存在一些问题  

1. **电机闭环控制和角度环控制：**还是没有达到视频大佬那种丝滑程度，甚至电机还有一点卡卡的感觉，可能闭环参数还需要一定的修改和调试
2. **识别的准确度：**卡片的识别准确度比较低，而且白天光线不均匀导致亮度变化，可能识别不太好，数据集已经拍了三分之一，还需要完善数据集和提高模型训练的准确度  
3. **边线矫正不及时：**OPENART的边线矫正有时候会很灵敏，但是有时候又会有一定的延迟，所以边线矫正也需要一定的优化，同时卡片还会导致边线矫正不准确，如果卡片数量较多的话，就会出现一侧同时有好几张重叠的卡片，不仅导致边线识别角度问题，同时也会不符合搬运规则，所以这个还需要再优化
4. **路径规划问题和搬运模式问题：**现在的路径规划就是找到最近的点位然后遍历，比较简单但是还是需要优化，然后搬运模式不知道是否需要优化，单搬可能速度比较慢，同时机械臂也需要比较准确的进行捡起卡片操作，防止没有搬运到，就非常可惜  

只能说现在完赛的希望比较大，争取能够完赛，然后在完赛的基础上再提速，也算是对得起自己半年的努力了  

## 2023/7/4  

目前对于目标检测遇见了一下问题，问题如下：  

1. 单个目标检测线程前一段功能好使，但是到了回到原来的位置就会出现问题，而且就算回到原来的位置也无法执行下一次遍历全图的操作  
2. 如果从别的线程进入目标检测线程，会出现小车乱飘，乱跑的现象，而且并不会开始进行遍历，这个还需要多次测试发现主要问题  

所以稍微捋一下思路，来解决这个问题，实现目标检测的思路是：  

1. 当接收到目标检测信号量之后，首先会到达上一次找到卡片的位置（第一次到达（40，40）），然后遍历全场
2. 如果在遍历的过程中接收到OPENART2发来的数据，就会先暂停遍历，向目标位置前进，矫正，识别，搬运
3. 如果完成**2**后，回到上一次发现卡片的位置，继续遍历全场

所以思路大概是：

1. 单片机接受到数据后，会有一个标志位，该标志位影响了遍历，卡片矫正时候的里程计矫正，同时也会让小车从遍历之中跳出来，前往卡片
2. OPENART发送的是卡片的x轴坐标和y轴坐标和距离标志位，两个坐标影响了小车如何运动到卡片的正前方，距离标志位表示的是是否移动到卡片预设距离
3. 单片机通过判读距离标志位，如果距离已经到达预设值，就停止运动，发送矫正信号量，并且开始识别搬运等任务
4. 实现以上任务之后，回到当初发现卡片的位置，继续遍历  

思路大概是这个样的，但是具体代码还有很多问题，需要实践发现问题并修改

## 2023/7/5

目前找到了目标检测的问题，主要是因为机械臂的角度，导致识别错了，所以必须及时连接到openart来发现问题，但是仍然存在一定的问题  

1. 找到卡片后，边线矫正会出现问题，不到达边线就矫正并且放下了卡片，而且回的位置也会非常离谱的不知道去哪了
2. 目标检测会将边线外的卡片也识别进去，可能可以调节结构来解决
3. 从别的函数进入目标检测线程的时候，也会出现问题，回归位置不对等等，还需要进行优化
4. **陀螺仪还是很漂**

基本上在七月七号之前解决以上问题基本上就可以实现完赛，之后就是优化准确率和提速

## 2023/7/7

已经换了新场地，调试了一下差不多能完赛了，主要问题大概有以下几点：  

1. 目标检测的时候会识别到舵机，需要优化舵机的姿态
2. 里程计会稍微有点不准（也有可能是小车启动甩尾导致的），这个可以用补偿或者是降速或者是调节好增量式pid，来让他更稳同时也更准
3. 识别准确度比较低

目标今天完赛，然后后面就可以进行提速，我觉得可以提速的地方有：

1. 机械臂的动作，如何让小车以很快的速度来捡起卡片，同时又能让卡片精准放在仓中，如何让小车准确且快速的将卡片丢下去
2. 运动的速度，小车的跑点速度，矫正速度，目标检测的速度

同时机械臂的动作很重要，现在就分析一下机械臂的动作

1. 转盘等待间隔，角度差为90°，180°和270°，额定转动时间需要测量，所以就需要角度差判断时间来控制机械臂

## 2023/7/13  

基本已经完赛，但是目标检测的速度还需要有待优化，同时对于决赛的分类也需要进行优化，在明天之前将其优化好，就可以宣告封车和完赛了。

## 2023/7/16

东北赛区已经结束，获得了第四名的成绩，应该能进国赛，但是很可惜没有进前三，不过已经很好了。  
不过结束也是开始，东北赛区结束了，但是下一个月就是全国总决赛了，时间还是很紧张的，

## 2023/7/20  

第二阶段要开始了,根据省赛的表现，其实发现还有很多问题可以修改，和强队亦有很大的差距，结构，硬件，控制，决策上都有很多问题，都需要修改  
主要修改以下问题：  

1. **结构问题**：结构需要做成六分类，同时还要打开舱门非常丝滑。同时摄像头支架需要非常稳定，需要一些支架来起支撑作用。机械臂的动作是否精准，能否将卡片准确放入仓内
2. **控制问题**：角度环够不够硬，启动速度够不够快，运行速度够不够快，矫正速度够不够快，同时矫正后机械臂落下的位置是否精准。
3. **视觉问题**：如何正确识别到边线，如果存在多个卡片在同一视野内如何改进只识别到一个，如何做好目标检测
4. **硬件问题**：由于六分类的设立，所以需要改变一些硬件设计，然后部分接线如何牢固连接，同时考虑继电器如何安装，板子也需要重新焊接
5. **决策问题**：如何实现拾取卡片，是否需要识别A4纸，还是直接全局遍历，如何稳定卸货和稳定回库等，还需要有待考虑。

## 2023/7/21

1. 添加了卡片识别只识别最近的卡片（未验证）
2. 添加了左右平移时的缓慢启动，防止速度过大导致平移会歪（也有可能平移时四个轮子的速度不同导致的会歪）（未验证）
3. 目标检测找色块找卡片，会识别到边线，能否通过确定色块的长度或者宽度等来排除边线，是否需要使用目标检测模型（未验证） 

## 2023/7/24

添加了六分类代码，但是没有进行测试，进行了结构的基本搭建，但是并不完全
对于目标检测全扫点的思路是：

1. 首先先遍历一次边线，如果找到卡片就记录当前里程计位置和卡片距离小车的远近  
2. 到达边线后，开始按照第一步找到的卡片的位置和卡片记录小车的远近来进行跑点，识别并且搬运卡片
3. 重复上述第二步骤，直至遍历全部并且到达上侧边线

难点：

1. 识别到新的卡片时候，如何判断此卡片是第一次被识别到
2. 如何准确识别横边线，来判断自己是否开始和到达边线，结束目标检测开始回库
3. 摄像头需要架什么样的角度，需要架多高，模型是否准确
4. 由于单目摄像头，识别到的卡片的位置并不是准确位置，如何准确找到卡片也需要考虑

逐渐将结构搭好，然后解决上述问题，并优化好回库和搬运函数，应该就可以取得比较好的成绩

解决办法：

1. 在每个检测周期，你可以保留最近检测到的卡片的位置，然后与下一个周期的最近卡片比较。如果两者之间的距离超过某个阈值，就可以判断为新的卡片。
2. 可以通过摄像头来判断是横线还是竖线，如果里程计较小，就不结束，里程计较大并且还是横线就结束（感觉不够完善）
3. 无
4. 大致可以通过摄像头得知位置，然后控制小车往大致方向运动，通过摄像头再进行矫正（需要大量的调试估计才行）如果视角有限的话，可以试试多个摄像头共同执行矫正的任务

## 2023/8/12

目前基本上能完成所有任务，但是存在一定的问题，主要问题还是目标检测的摄像头问题，无法识别到想要的视野内的所有卡片，会漏卡片，同时也会多次在同一地方检测到多次卡片，卡片平行的话无法同时识别到两张卡片，修改的办法主要应该是目标检测的范围，目标检测的时间间隔和单片机对于检测数据的处理，这个还需要反复调试来找到最优的解。

## 2023/8/19

现在是凌晨两点二十四，回想昨天的国赛初赛出了点问题，没有完赛，没有奖项，自己八个多月辛辛苦苦的努力最终以这种意难平的结局结束，躺在床上辗转反侧无法入睡，非常惆怅。
主要问题应该是没有第一时间适应好场地的因素，由于比赛场地比实验室的亮很多，OpenArt的补光微乎其微，同时调节卡片阈值没有调节好，更因为矫正做的不好等等问题，在最后一刻问题都出现了，即使在实验室里跑的再出色，但是比赛上出现了问题就是出现了问题，主要也是自己水平不太够，心不够稳，没有第一时间找到问题所在并且修改他，而是慌了手脚。  
不知道这是否是我此生仅有的机会了，很遗憾，很难克服自己长久的付出和努力与最终实际取得的成果不一致的落差感。虽说过程重要，但是没有了最终的结果还是那么的黯然。  
不过就像省赛所说的，结束也是另一种开始，哥们也体验了进入国赛的兴奋，国赛失败的落魄，权当是一种经历了，虽然这种经历并不是自己想看到的。事已至此，已经圆满了，从去年十一月份开始到今天，也算是给我大二生涯画上了一个句号。还是非常感谢智能车这个比赛，遇见了很多志同道合的，非常厉害并且善于分享和交流的同学，非常感谢那些曾帮助过我设计板子，设计结构，分享调车经验，找场地，给予精神支持的学长学姐们，感谢他们的帮助，能使我有机会站在国赛的赛场上。  
不管怎么说，我一定会怀着当初对于技术，对于比赛，对于学习的热爱和激情，继续走下去的。