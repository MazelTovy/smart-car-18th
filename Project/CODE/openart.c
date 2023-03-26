#include "openart.h"

// 串口收发个字母的含义
// 发'G' ART1开始识别
// 收'A' ART1坐标帧头
// 收'Y' ART1坐标帧尾
// 收'I' ART1图片种类帧头
// 收'J' ART1图片种类帧尾
// 收'C' ART1纠正角度帧头
// 收'D' ART1纠正角度帧尾 也是识别成功标志位

uint8 ART1_uart_rx_buffer;
lpuart_transfer_t ART1_receivexfer;
lpuart_handle_t ART1_g_lpuartHandle;

uint8 ART1_dat[82]; // 前一半x后一半y
uint8 ART1_POINT_X[40];
uint8 ART1_POINT_Y[40];
uint8 point_num = 0; // 数据个数

rt_sem_t point_sem;
//rt_sem_t key2_sem;
//rt_sem_t key3_sem;
//rt_sem_t key4_sem;



void ART1_uart_callback(LPUART_Type *base, lpuart_handle_t *handle, status_t status, void *userData)
{

	static uint8 rxstate = 0;

	static uint8 recive_flag = 0;
	static uint8 ART1_POINT_i,ART1_POINT_j=0;	

	if (kStatus_LPUART_RxIdle == status)
	{
	

		if(rxstate == 0)
		{
			if (ART1_uart_rx_buffer == 'A') // 接受到帧头
			{
				rxstate = 1;
				point_num = 0;
			}
		}
		else if(rxstate == 1)
		{
			if(ART1_uart_rx_buffer == 'Y')
			{
				for (int temp = 0; temp<point_num; temp++)
				{
					if(temp < point_num/2)
					{
						ART1_POINT_X[temp] = ART1_dat[temp];
//						rt_kprintf("%d\n", ART1_dat[temp]);
					}else
					{
						ART1_POINT_Y[temp-point_num/2] = ART1_dat[temp];
//					rt_kprintf("%d\n", ART1_dat[temp]);
					}//		
						
						 
				}
				rt_sem_release(point_sem);
				rxstate = 0;
//				uart_coordinate_transforming(ART1_POINT_X,ART1_POINT_Y, point_num/2);

			}
			else
			{
				ART1_dat[point_num] = ART1_uart_rx_buffer;
//				rt_kprintf("%d\n", ART1_dat[point_num]);
				point_num++; // 统计接到数据的个数  前二分之一为x坐标， 后二分之一为y坐标
			}
			
		}

		
	}

	handle->rxDataSize = ART1_receivexfer.dataSize; // 还原缓冲区长度
	handle->rxData = ART1_receivexfer.data;			// 还原缓冲区地址
}

void ART1_UART_Init(void)
{
	uart_init(USART_4, 115200, UART4_TX_C16, UART4_RX_C17);
	NVIC_SetPriority(LPUART4_IRQn, 3); // 设置串口中断优先级 范围0-15 越小优先级越高
	uart_rx_irq(USART_4, 1);
	uart_tx_irq(USART_4, 1);
	// 配置串口接收的缓冲区及缓冲区长度
	ART1_receivexfer.dataSize = 1;
	ART1_receivexfer.data = &ART1_uart_rx_buffer;
	// 设置中断函数及其参数
	uart_set_handle(USART_4, &ART1_g_lpuartHandle, ART1_uart_callback, NULL, 0, ART1_receivexfer.data, 1);
}