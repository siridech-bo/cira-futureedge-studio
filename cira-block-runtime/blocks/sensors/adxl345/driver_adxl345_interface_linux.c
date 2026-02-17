/**
 * @file      driver_adxl345_interface_linux.c
 * @brief     Linux/Jetson interface implementation for ADXL345
 * @version   1.0.0
 * @date      2024
 *
 * This file implements the libdriver ADXL345 interface functions
 * for Linux systems (including Jetson Nano/Xavier).
 * Supports both I2C and SPI communication.
 */

#include "libdriver/interface/driver_adxl345_interface.h"

#ifdef __linux__

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <linux/i2c-dev.h>
#include <linux/spi/spidev.h>
#include <time.h>

/* I2C configuration */
static int g_i2c_fd = -1;
static const char *g_i2c_device = "/dev/i2c-1";

/* SPI configuration */
static int g_spi_fd = -1;
static const char *g_spi_device = "/dev/spidev0.0";
static uint32_t g_spi_speed = 5000000;  /* 5 MHz */
static uint8_t g_spi_mode = SPI_MODE_3;
static uint8_t g_spi_bits = 8;

/* Debug output enable flag */
static int g_debug_enabled = 1;

/**
 * @brief  Set I2C device path
 * @param[in] device path (e.g., "/dev/i2c-1")
 */
void adxl345_interface_set_i2c_device(const char *device)
{
    g_i2c_device = device;
}

/**
 * @brief  Set SPI device path
 * @param[in] device path (e.g., "/dev/spidev0.0")
 */
void adxl345_interface_set_spi_device(const char *device)
{
    g_spi_device = device;
}

/**
 * @brief  Set SPI speed
 * @param[in] speed in Hz
 */
void adxl345_interface_set_spi_speed(uint32_t speed)
{
    g_spi_speed = speed;
}

/**
 * @brief  Enable/disable debug output
 * @param[in] enable 1 to enable, 0 to disable
 */
void adxl345_interface_set_debug(int enable)
{
    g_debug_enabled = enable;
}

/**
 * @brief  interface iic bus init
 * @return status code
 *         - 0 success
 *         - 1 iic init failed
 */
uint8_t adxl345_interface_iic_init(void)
{
    g_i2c_fd = open(g_i2c_device, O_RDWR);
    if (g_i2c_fd < 0)
    {
        adxl345_interface_debug_print("adxl345: failed to open I2C device %s\n", g_i2c_device);
        return 1;
    }

    adxl345_interface_debug_print("adxl345: I2C initialized on %s\n", g_i2c_device);
    return 0;
}

/**
 * @brief  interface iic bus deinit
 * @return status code
 *         - 0 success
 *         - 1 iic deinit failed
 */
uint8_t adxl345_interface_iic_deinit(void)
{
    if (g_i2c_fd >= 0)
    {
        close(g_i2c_fd);
        g_i2c_fd = -1;
        adxl345_interface_debug_print("adxl345: I2C deinitialized\n");
    }
    return 0;
}

/**
 * @brief      interface iic bus read
 * @param[in]  addr iic device write address
 * @param[in]  reg iic register address
 * @param[out] *buf pointer to a data buffer
 * @param[in]  len length of the data buffer
 * @return     status code
 *             - 0 success
 *             - 1 read failed
 */
uint8_t adxl345_interface_iic_read(uint8_t addr, uint8_t reg, uint8_t *buf, uint16_t len)
{
    if (g_i2c_fd < 0)
    {
        return 1;
    }

    /* Set I2C slave address (convert from 8-bit to 7-bit) */
    if (ioctl(g_i2c_fd, I2C_SLAVE, addr >> 1) < 0)
    {
        adxl345_interface_debug_print("adxl345: failed to set I2C slave address 0x%02X\n", addr >> 1);
        return 1;
    }

    /* Write register address */
    if (write(g_i2c_fd, &reg, 1) != 1)
    {
        adxl345_interface_debug_print("adxl345: failed to write register address 0x%02X\n", reg);
        return 1;
    }

    /* Read data */
    if (read(g_i2c_fd, buf, len) != (ssize_t)len)
    {
        adxl345_interface_debug_print("adxl345: failed to read %d bytes from register 0x%02X\n", len, reg);
        return 1;
    }

    return 0;
}

/**
 * @brief     interface iic bus write
 * @param[in] addr iic device write address
 * @param[in] reg iic register address
 * @param[in] *buf pointer to a data buffer
 * @param[in] len length of the data buffer
 * @return    status code
 *            - 0 success
 *            - 1 write failed
 */
uint8_t adxl345_interface_iic_write(uint8_t addr, uint8_t reg, uint8_t *buf, uint16_t len)
{
    if (g_i2c_fd < 0)
    {
        return 1;
    }

    /* Set I2C slave address (convert from 8-bit to 7-bit) */
    if (ioctl(g_i2c_fd, I2C_SLAVE, addr >> 1) < 0)
    {
        adxl345_interface_debug_print("adxl345: failed to set I2C slave address 0x%02X\n", addr >> 1);
        return 1;
    }

    /* Prepare buffer with register address + data */
    uint8_t *write_buf = (uint8_t *)malloc(len + 1);
    if (write_buf == NULL)
    {
        return 1;
    }

    write_buf[0] = reg;
    memcpy(write_buf + 1, buf, len);

    /* Write register address and data */
    ssize_t ret = write(g_i2c_fd, write_buf, len + 1);
    free(write_buf);

    if (ret != (ssize_t)(len + 1))
    {
        adxl345_interface_debug_print("adxl345: failed to write %d bytes to register 0x%02X\n", len, reg);
        return 1;
    }

    return 0;
}

/**
 * @brief  interface spi bus init
 * @return status code
 *         - 0 success
 *         - 1 spi init failed
 */
uint8_t adxl345_interface_spi_init(void)
{
    g_spi_fd = open(g_spi_device, O_RDWR);
    if (g_spi_fd < 0)
    {
        adxl345_interface_debug_print("adxl345: failed to open SPI device %s\n", g_spi_device);
        return 1;
    }

    /* Set SPI mode */
    if (ioctl(g_spi_fd, SPI_IOC_WR_MODE, &g_spi_mode) < 0)
    {
        adxl345_interface_debug_print("adxl345: failed to set SPI mode\n");
        close(g_spi_fd);
        g_spi_fd = -1;
        return 1;
    }

    /* Set bits per word */
    if (ioctl(g_spi_fd, SPI_IOC_WR_BITS_PER_WORD, &g_spi_bits) < 0)
    {
        adxl345_interface_debug_print("adxl345: failed to set SPI bits per word\n");
        close(g_spi_fd);
        g_spi_fd = -1;
        return 1;
    }

    /* Set max speed */
    if (ioctl(g_spi_fd, SPI_IOC_WR_MAX_SPEED_HZ, &g_spi_speed) < 0)
    {
        adxl345_interface_debug_print("adxl345: failed to set SPI speed\n");
        close(g_spi_fd);
        g_spi_fd = -1;
        return 1;
    }

    adxl345_interface_debug_print("adxl345: SPI initialized on %s at %d Hz\n", g_spi_device, g_spi_speed);
    return 0;
}

/**
 * @brief  interface spi bus deinit
 * @return status code
 *         - 0 success
 *         - 1 spi deinit failed
 */
uint8_t adxl345_interface_spi_deinit(void)
{
    if (g_spi_fd >= 0)
    {
        close(g_spi_fd);
        g_spi_fd = -1;
        adxl345_interface_debug_print("adxl345: SPI deinitialized\n");
    }
    return 0;
}

/**
 * @brief      interface spi bus read
 * @param[in]  reg register address
 * @param[out] *buf pointer to a data buffer
 * @param[in]  len length of data buffer
 * @return     status code
 *             - 0 success
 *             - 1 read failed
 */
uint8_t adxl345_interface_spi_read(uint8_t reg, uint8_t *buf, uint16_t len)
{
    if (g_spi_fd < 0)
    {
        return 1;
    }

    /* ADXL345 SPI read: set bit 7 (read) and bit 6 (multi-byte) if len > 1 */
    uint8_t cmd = reg | 0x80;  /* Read bit */
    if (len > 1)
    {
        cmd |= 0x40;  /* Multi-byte bit */
    }

    /* Prepare TX/RX buffers */
    uint8_t *tx_buf = (uint8_t *)calloc(len + 1, 1);
    uint8_t *rx_buf = (uint8_t *)calloc(len + 1, 1);
    if (tx_buf == NULL || rx_buf == NULL)
    {
        free(tx_buf);
        free(rx_buf);
        return 1;
    }

    tx_buf[0] = cmd;

    struct spi_ioc_transfer tr = {
        .tx_buf = (unsigned long)tx_buf,
        .rx_buf = (unsigned long)rx_buf,
        .len = len + 1,
        .speed_hz = g_spi_speed,
        .bits_per_word = g_spi_bits,
        .delay_usecs = 0,
    };

    if (ioctl(g_spi_fd, SPI_IOC_MESSAGE(1), &tr) < 0)
    {
        adxl345_interface_debug_print("adxl345: SPI read failed for register 0x%02X\n", reg);
        free(tx_buf);
        free(rx_buf);
        return 1;
    }

    /* Copy received data (skip first byte which is during command send) */
    memcpy(buf, rx_buf + 1, len);

    free(tx_buf);
    free(rx_buf);
    return 0;
}

/**
 * @brief     interface spi bus write
 * @param[in] reg register address
 * @param[in] *buf pointer to a data buffer
 * @param[in] len length of data buffer
 * @return    status code
 *            - 0 success
 *            - 1 write failed
 */
uint8_t adxl345_interface_spi_write(uint8_t reg, uint8_t *buf, uint16_t len)
{
    if (g_spi_fd < 0)
    {
        return 1;
    }

    /* ADXL345 SPI write: bit 7 = 0, set bit 6 (multi-byte) if len > 1 */
    uint8_t cmd = reg & 0x3F;  /* Clear read bit */
    if (len > 1)
    {
        cmd |= 0x40;  /* Multi-byte bit */
    }

    /* Prepare TX buffer */
    uint8_t *tx_buf = (uint8_t *)malloc(len + 1);
    if (tx_buf == NULL)
    {
        return 1;
    }

    tx_buf[0] = cmd;
    memcpy(tx_buf + 1, buf, len);

    struct spi_ioc_transfer tr = {
        .tx_buf = (unsigned long)tx_buf,
        .rx_buf = 0,
        .len = len + 1,
        .speed_hz = g_spi_speed,
        .bits_per_word = g_spi_bits,
        .delay_usecs = 0,
    };

    int ret = ioctl(g_spi_fd, SPI_IOC_MESSAGE(1), &tr);
    free(tx_buf);

    if (ret < 0)
    {
        adxl345_interface_debug_print("adxl345: SPI write failed for register 0x%02X\n", reg);
        return 1;
    }

    return 0;
}

/**
 * @brief     interface delay ms
 * @param[in] ms time
 */
void adxl345_interface_delay_ms(uint32_t ms)
{
    struct timespec ts;
    ts.tv_sec = ms / 1000;
    ts.tv_nsec = (ms % 1000) * 1000000L;
    nanosleep(&ts, NULL);
}

/**
 * @brief     interface print format data
 * @param[in] fmt format data
 */
void adxl345_interface_debug_print(const char *const fmt, ...)
{
    if (g_debug_enabled)
    {
        va_list args;
        va_start(args, fmt);
        vprintf(fmt, args);
        va_end(args);
    }
}

/**
 * @brief     interface receive callback
 * @param[in] type irq type
 */
void adxl345_interface_receive_callback(uint8_t type)
{
    switch (type)
    {
        case ADXL345_INTERRUPT_DATA_READY:
            adxl345_interface_debug_print("adxl345: irq data ready\n");
            break;
        case ADXL345_INTERRUPT_SINGLE_TAP:
            adxl345_interface_debug_print("adxl345: irq single tap\n");
            break;
        case ADXL345_INTERRUPT_DOUBLE_TAP:
            adxl345_interface_debug_print("adxl345: irq double tap\n");
            break;
        case ADXL345_INTERRUPT_ACTIVITY:
            adxl345_interface_debug_print("adxl345: irq activity\n");
            break;
        case ADXL345_INTERRUPT_INACTIVITY:
            adxl345_interface_debug_print("adxl345: irq inactivity\n");
            break;
        case ADXL345_INTERRUPT_FREE_FALL:
            adxl345_interface_debug_print("adxl345: irq free fall\n");
            break;
        case ADXL345_INTERRUPT_WATERMARK:
            adxl345_interface_debug_print("adxl345: irq watermark\n");
            break;
        case ADXL345_INTERRUPT_OVERRUN:
            adxl345_interface_debug_print("adxl345: irq overrun\n");
            break;
        default:
            adxl345_interface_debug_print("adxl345: unknown irq type %d\n", type);
            break;
    }
}

#else /* Non-Linux systems - stub implementation */

uint8_t adxl345_interface_iic_init(void) { return 1; }
uint8_t adxl345_interface_iic_deinit(void) { return 0; }
uint8_t adxl345_interface_iic_read(uint8_t addr, uint8_t reg, uint8_t *buf, uint16_t len) { return 1; }
uint8_t adxl345_interface_iic_write(uint8_t addr, uint8_t reg, uint8_t *buf, uint16_t len) { return 1; }
uint8_t adxl345_interface_spi_init(void) { return 1; }
uint8_t adxl345_interface_spi_deinit(void) { return 0; }
uint8_t adxl345_interface_spi_read(uint8_t reg, uint8_t *buf, uint16_t len) { return 1; }
uint8_t adxl345_interface_spi_write(uint8_t reg, uint8_t *buf, uint16_t len) { return 1; }
void adxl345_interface_delay_ms(uint32_t ms) { (void)ms; }
void adxl345_interface_debug_print(const char *const fmt, ...) { (void)fmt; }
void adxl345_interface_receive_callback(uint8_t type) { (void)type; }

#endif /* __linux__ */
