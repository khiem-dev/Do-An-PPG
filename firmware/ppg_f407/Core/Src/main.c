/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2026 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include <stdio.h>
#include <string.h>
#include "dsp_nlms.h"
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
#define MAX30102_ADDR      (0x57 << 1)   /* HAL dung dia chi 7-bit dich trai 1 */

#define REG_INTR_ENABLE_1  0x02
#define REG_INTR_ENABLE_2  0x03
#define REG_FIFO_WR_PTR    0x04
#define REG_OVF_COUNTER    0x05
#define REG_FIFO_RD_PTR    0x06
#define REG_FIFO_DATA      0x07
#define REG_FIFO_CONFIG    0x08
#define REG_MODE_CONFIG    0x09
#define REG_SPO2_CONFIG    0x0A
#define REG_LED1_PA        0x0C          /* Red */
#define REG_LED2_PA        0x0D          /* IR  */
#define REG_PART_ID        0xFF          /* doc ra 0x15 neu dung MAX30102 */

#define USE_OLED           1             /* dat 0 khi THU DU LIEU de dong bo PPG-gia toc tot hon */

/* MPU6050 (AD0 de trong / noi GND -> 0x68) */
#define MPU_ADDR           (0x68 << 1)
#define MPU_REG_SMPLRT_DIV 0x19
#define MPU_REG_CONFIG     0x1A
#define MPU_REG_ACCEL_CFG  0x1C
#define MPU_REG_ACCEL_OUT  0x3B
#define MPU_REG_PWR_MGMT_1 0x6B
#define MPU_REG_WHO_AM_I   0x75

#define OLED_ADDR          (0x3C << 1)   /* SSD1306; mot so module la 0x3D */
#define OLED_W             128
#define OLED_H             64
#define WAVE_LEN           128
/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/
I2C_HandleTypeDef hi2c1;

UART_HandleTypeDef huart2;

/* USER CODE BEGIN PV */

/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_I2C1_Init(void);
static void MX_USART2_UART_Init(void);
/* USER CODE BEGIN PFP */

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */
/* Cho phep printf() gui qua USART2 */
int __io_putchar(int ch)
{
    ITM_SendChar(ch);                      /* xem bang SWV; khong bat SWV thi bo qua */
    HAL_UART_Transmit(&huart2, (uint8_t *)&ch, 1, 10);   /* gui qua USB-TTL (PA2) */
    return ch;
}

static HAL_StatusTypeDef max_write(uint8_t reg, uint8_t val)
{
    return HAL_I2C_Mem_Write(&hi2c1, MAX30102_ADDR, reg, I2C_MEMADD_SIZE_8BIT, &val, 1, 50);
}

static HAL_StatusTypeDef max_read(uint8_t reg, uint8_t *buf, uint16_t len)
{
    return HAL_I2C_Mem_Read(&hi2c1, MAX30102_ADDR, reg, I2C_MEMADD_SIZE_8BIT, buf, len, 50);
}

static void i2c_scan(void)
{
    printf("Quet I2C...\r\n");
    int found = 0;
    for (uint8_t a = 1; a < 128; a++) {
        if (HAL_I2C_IsDeviceReady(&hi2c1, a << 1, 1, 10) == HAL_OK) {
            printf("  Thay thiet bi tai 0x%02X\r\n", a);
            found++;
        }
    }
    if (!found) printf("  Khong thay thiet bi nao. Kiem tra day, nguon 3V, SCL/SDA.\r\n");
}

static int max30102_init(void)
{
    uint8_t id = 0;
    if (max_read(REG_PART_ID, &id, 1) != HAL_OK) return -1;
    printf("PART_ID = 0x%02X (mong doi 0x15)\r\n", id);
    if (id != 0x15) return -2;

    max_write(REG_MODE_CONFIG, 0x40);      /* reset */
    HAL_Delay(100);

    max_write(REG_INTR_ENABLE_1, 0x00);    /* khong dung ngat */
    max_write(REG_INTR_ENABLE_2, 0x00);
    max_write(REG_FIFO_WR_PTR, 0x00);      /* xoa con tro FIFO */
    max_write(REG_OVF_COUNTER, 0x00);
    max_write(REG_FIFO_RD_PTR, 0x00);

    max_write(REG_FIFO_CONFIG, 0x10);      /* khong trung binh, rollover bat */
    max_write(REG_SPO2_CONFIG, 0x27);      /* ADC 4096nA, 100 Hz, 18-bit */
    max_write(REG_LED1_PA, 0x24);          /* LED Red ~7 mA */
    max_write(REG_LED2_PA, 0x24);          /* LED IR  ~7 mA */
    max_write(REG_MODE_CONFIG, 0x03);      /* che do SpO2: Red + IR */
    return 0;
}

/* Doc tat ca mau dang co trong FIFO, in ra "index,red,ir" */
/* ---------------- MPU6050 ---------------- */
static int16_t g_ax = 0, g_ay = 0, g_az = 0;   /* gia tri tho; +-4g -> 8192 LSB/g */

static int mpu6050_init(void)
{
    uint8_t id = 0, v;
    if (HAL_I2C_Mem_Read(&hi2c1, MPU_ADDR, MPU_REG_WHO_AM_I, I2C_MEMADD_SIZE_8BIT, &id, 1, 50) != HAL_OK)
        return -1;
    printf("MPU6050 WHO_AM_I = 0x%02X (mong doi 0x68)\r\n", id);
    if (id != 0x68) return -2;
    v = 0x00; HAL_I2C_Mem_Write(&hi2c1, MPU_ADDR, MPU_REG_PWR_MGMT_1, I2C_MEMADD_SIZE_8BIT, &v, 1, 50); /* danh thuc */
    HAL_Delay(50);
    v = 0x03; HAL_I2C_Mem_Write(&hi2c1, MPU_ADDR, MPU_REG_CONFIG,     I2C_MEMADD_SIZE_8BIT, &v, 1, 50); /* loc so ~44 Hz */
    v = 0x07; HAL_I2C_Mem_Write(&hi2c1, MPU_ADDR, MPU_REG_SMPLRT_DIV, I2C_MEMADD_SIZE_8BIT, &v, 1, 50); /* 1 kHz/8 = 125 Hz noi bo */
    v = 0x08; HAL_I2C_Mem_Write(&hi2c1, MPU_ADDR, MPU_REG_ACCEL_CFG,  I2C_MEMADD_SIZE_8BIT, &v, 1, 50); /* +-4g */
    return 0;
}

static void mpu6050_read(void)
{
    uint8_t b[6];
    if (HAL_I2C_Mem_Read(&hi2c1, MPU_ADDR, MPU_REG_ACCEL_OUT, I2C_MEMADD_SIZE_8BIT, b, 6, 50) != HAL_OK) return;
    g_ax = (int16_t)((b[0] << 8) | b[1]);
    g_ay = (int16_t)((b[2] << 8) | b[3]);
    g_az = (int16_t)((b[4] << 8) | b[5]);
}

static uint32_t g_red = 0, g_ir = 0;
static uint32_t wave[WAVE_LEN];
static uint32_t wave_cnt = 0;
static PPG_NLMS g_nlms;
static float g_ppg_bp = 0.0f, g_ppg_nlms = 0.0f;

static void max30102_poll_and_print(void)
{
    static uint32_t idx = 0;
    uint8_t wr, rd;
    if (max_read(REG_FIFO_WR_PTR, &wr, 1) != HAL_OK) return;
    if (max_read(REG_FIFO_RD_PTR, &rd, 1) != HAL_OK) return;

    int n = (wr - rd) & 0x1F;              /* FIFO 32 mau */
    while (n--) {
        uint8_t b[6];
        if (max_read(REG_FIFO_DATA, b, 6) != HAL_OK) return;
        uint32_t red = (((uint32_t)b[0] << 16) | ((uint32_t)b[1] << 8) | b[2]) & 0x3FFFF;
        uint32_t ir  = (((uint32_t)b[3] << 16) | ((uint32_t)b[4] << 8) | b[5]) & 0x3FFFF;
        g_red = red; g_ir = ir;
        g_ppg_nlms = ppg_nlms_step(&g_nlms, (float)ir, g_ax, g_ay, g_az, &g_ppg_bp);
        if ((idx & 1) == 0) {              /* lay 1 trong 2 mau: song dai ~2.5 s */
            wave[wave_cnt % WAVE_LEN] = ir;
            wave_cnt++;
        }
        printf("%lu,%lu,%lu,%d,%d,%d\r\n", (unsigned long)idx++, (unsigned long)red, (unsigned long)ir,
               g_ax, g_ay, g_az);
    }
}

/* ---------------- OLED SSD1306 128x64 (I2C) ---------------- */
static uint8_t oled_buf[OLED_W * OLED_H / 8];
static int oled_ok = 0;

/* Font 5x7, moi cot 1 byte, bit0 la hang tren cung. Chi gom ky tu can dung. */
static const uint8_t *glyph(char c)
{
    static const uint8_t g_digits[10][5] = {
        {0x3E,0x51,0x49,0x45,0x3E}, {0x00,0x42,0x7F,0x40,0x00},
        {0x42,0x61,0x51,0x49,0x46}, {0x21,0x41,0x45,0x4B,0x31},
        {0x18,0x14,0x12,0x7F,0x10}, {0x27,0x45,0x45,0x45,0x39},
        {0x3C,0x4A,0x49,0x49,0x30}, {0x01,0x71,0x09,0x05,0x03},
        {0x36,0x49,0x49,0x49,0x36}, {0x06,0x49,0x49,0x29,0x1E}};
    static const uint8_t g_colon[5] = {0x00,0x36,0x36,0x00,0x00};
    static const uint8_t g_I[5]     = {0x00,0x41,0x7F,0x41,0x00};
    static const uint8_t g_R[5]     = {0x7F,0x09,0x19,0x29,0x46};
    static const uint8_t g_blank[5] = {0,0,0,0,0};
    if (c >= '0' && c <= '9') return g_digits[c - '0'];
    if (c == ':') return g_colon;
    if (c == 'I') return g_I;
    if (c == 'R') return g_R;
    return g_blank;
}

static void oled_cmd(uint8_t c)
{
    HAL_I2C_Mem_Write(&hi2c1, OLED_ADDR, 0x00, I2C_MEMADD_SIZE_8BIT, &c, 1, 50);
}

static int oled_init(void)
{
    if (HAL_I2C_IsDeviceReady(&hi2c1, OLED_ADDR, 2, 20) != HAL_OK) return -1;
    static const uint8_t seq[] = {
        0xAE, 0xD5,0x80, 0xA8,0x3F, 0xD3,0x00, 0x40, 0x8D,0x14,
        0x20,0x00, 0xA1, 0xC8, 0xDA,0x12, 0x81,0xCF, 0xD9,0xF1,
        0xDB,0x40, 0xA4, 0xA6, 0xAF };
    for (unsigned i = 0; i < sizeof(seq); i++) oled_cmd(seq[i]);
    memset(oled_buf, 0, sizeof(oled_buf));
    return 0;
}

static void oled_update(void)
{
    oled_cmd(0x21); oled_cmd(0); oled_cmd(127);   /* cot 0..127 */
    oled_cmd(0x22); oled_cmd(0); oled_cmd(7);     /* trang 0..7 */
    HAL_I2C_Mem_Write(&hi2c1, OLED_ADDR, 0x40, I2C_MEMADD_SIZE_8BIT,
                      oled_buf, sizeof(oled_buf), 200);
}

static void oled_pixel(int x, int y)
{
    if (x < 0 || x >= OLED_W || y < 0 || y >= OLED_H) return;
    oled_buf[x + (y >> 3) * OLED_W] |= (1 << (y & 7));
}

static void oled_text(int x, int y, const char *s)
{
    for (; *s; s++, x += 6) {
        const uint8_t *g = glyph(*s);
        for (int cx = 0; cx < 5; cx++)
            for (int cy = 0; cy < 7; cy++)
                if (g[cx] & (1 << cy)) oled_pixel(x + cx, y + cy);
    }
}

/* Ve: dong 1 = IR, dong 2 = Red, phan duoi = song xung IR */
static void oled_draw(void)
{
    char line[24];
    memset(oled_buf, 0, sizeof(oled_buf));
    snprintf(line, sizeof(line), "IR:%lu HR:%d", (unsigned long)g_ir, (int)(g_nlms.hr_bpm + 0.5f));
    oled_text(0, 0, line);
    snprintf(line, sizeof(line), "R:%lu", (unsigned long)g_red);
    oled_text(0, 8, line);

    int n = (wave_cnt < WAVE_LEN) ? (int)wave_cnt : WAVE_LEN;
    if (n < 2) return;
    uint32_t mn = 0xFFFFFFFF, mx = 0;
    for (int i = 0; i < n; i++) {
        uint32_t v = wave[(wave_cnt - n + i) % WAVE_LEN];
        if (v < mn) mn = v;
        if (v > mx) mx = v;
    }
    uint32_t range = (mx > mn) ? (mx - mn) : 1;
    int prev_y = -1;
    for (int i = 0; i < n; i++) {
        uint32_t v = wave[(wave_cnt - n + i) % WAVE_LEN];
        int y = 63 - (int)(((uint64_t)(v - mn) * 46) / range);   /* vung y = 17..63 */
        int y0 = (prev_y < 0) ? y : prev_y;
        int a = (y0 < y) ? y0 : y, b = (y0 < y) ? y : y0;
        for (int yy = a; yy <= b; yy++) oled_pixel(i, yy);
        prev_y = y;
    }
}
/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{

  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_I2C1_Init();
  MX_USART2_UART_Init();
  /* USER CODE BEGIN 2 */
  setvbuf(stdout, NULL, _IONBF, 0);        /* in ra UART ngay, khong dem */
  ppg_nlms_init(&g_nlms);
  HAL_Delay(500);
  i2c_scan();
  oled_ok = (oled_init() == 0);
  printf(oled_ok ? "OLED OK\r\n" : "Khong thay OLED (0x3C)\r\n");
  if (mpu6050_init() != 0) printf("Khoi tao MPU6050 loi!\r\n");
  else                     printf("MPU6050 OK\r\n");
  if (max30102_init() != 0) {
      printf("Khoi tao MAX30102 loi!\r\n");
  } else {
      printf("MAX30102 OK. Du lieu: index,red,ir,ax,ay,az\r\n");
  }
  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
    static uint32_t next_tick = 0;
    uint32_t now = HAL_GetTick();
    if (now >= next_tick) {
        next_tick += 10;                       /* chu ky 10 ms = 100 Hz */
        if (now > next_tick + 10) next_tick = now + 10;   /* bi tre (vd. dang ve OLED): dong bo lai */
        mpu6050_read();                        /* gia toc ngay truoc khi doc FIFO PPG */
        max30102_poll_and_print();
    }
#if USE_OLED
    if (oled_ok) {
        static uint32_t t_oled = 0;
        if (now - t_oled >= 500) {             /* ve OLED moi 0.5 s de it lam tre viec lay mau */
            t_oled = now;
            oled_draw();
            oled_update();
        }
    }
#endif
  }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  /** Configure the main internal regulator output voltage
  */
  __HAL_RCC_PWR_CLK_ENABLE();
  __HAL_PWR_VOLTAGESCALING_CONFIG(PWR_REGULATOR_VOLTAGE_SCALE1);

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSI;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_NONE;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_HSI;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV1;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_0) != HAL_OK)
  {
    Error_Handler();
  }
}

/**
  * @brief I2C1 Initialization Function
  * @param None
  * @retval None
  */
static void MX_I2C1_Init(void)
{

  /* USER CODE BEGIN I2C1_Init 0 */

  /* USER CODE END I2C1_Init 0 */

  /* USER CODE BEGIN I2C1_Init 1 */

  /* USER CODE END I2C1_Init 1 */
  hi2c1.Instance = I2C1;
  hi2c1.Init.ClockSpeed = 400000;
  hi2c1.Init.DutyCycle = I2C_DUTYCYCLE_2;
  hi2c1.Init.OwnAddress1 = 0;
  hi2c1.Init.AddressingMode = I2C_ADDRESSINGMODE_7BIT;
  hi2c1.Init.DualAddressMode = I2C_DUALADDRESS_DISABLE;
  hi2c1.Init.OwnAddress2 = 0;
  hi2c1.Init.GeneralCallMode = I2C_GENERALCALL_DISABLE;
  hi2c1.Init.NoStretchMode = I2C_NOSTRETCH_DISABLE;
  if (HAL_I2C_Init(&hi2c1) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN I2C1_Init 2 */

  /* USER CODE END I2C1_Init 2 */

}

/**
  * @brief USART2 Initialization Function
  * @param None
  * @retval None
  */
static void MX_USART2_UART_Init(void)
{

  /* USER CODE BEGIN USART2_Init 0 */

  /* USER CODE END USART2_Init 0 */

  /* USER CODE BEGIN USART2_Init 1 */

  /* USER CODE END USART2_Init 1 */
  huart2.Instance = USART2;
  huart2.Init.BaudRate = 115200;
  huart2.Init.WordLength = UART_WORDLENGTH_8B;
  huart2.Init.StopBits = UART_STOPBITS_1;
  huart2.Init.Parity = UART_PARITY_NONE;
  huart2.Init.Mode = UART_MODE_TX_RX;
  huart2.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  huart2.Init.OverSampling = UART_OVERSAMPLING_16;
  if (HAL_UART_Init(&huart2) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN USART2_Init 2 */

  /* USER CODE END USART2_Init 2 */

}

/**
  * @brief GPIO Initialization Function
  * @param None
  * @retval None
  */
static void MX_GPIO_Init(void)
{
  /* USER CODE BEGIN MX_GPIO_Init_1 */

  /* USER CODE END MX_GPIO_Init_1 */

  /* GPIO Ports Clock Enable */
  __HAL_RCC_GPIOH_CLK_ENABLE();
  __HAL_RCC_GPIOA_CLK_ENABLE();
  __HAL_RCC_GPIOB_CLK_ENABLE();

  /* USER CODE BEGIN MX_GPIO_Init_2 */

  /* USER CODE END MX_GPIO_Init_2 */
}

/* USER CODE BEGIN 4 */

/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}
#ifdef USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
