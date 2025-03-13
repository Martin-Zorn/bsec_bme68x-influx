/**********************************************************************************************************************/
/* header files */
/**********************************************************************************************************************/
#define _POSIX_C_SOURCE 199309L

#include "bsec_integration.h"
#include <fcntl.h>
#include <inttypes.h>
#include <linux/i2c-dev.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <sys/types.h>
#include <time.h>
#include <unistd.h>

/**********************************************************************************************************************/
/* globals */
/**********************************************************************************************************************/

int g_i2c_fd;
int i2c_address = 0x77;
char *filename_state = "bsec_iaq.state";
char *filename_config = "bsec_iaq.config";

uint32_t overflowCounter;
uint32_t lastTimeMS;

/**********************************************************************************************************************/
/* functions */
/**********************************************************************************************************************/

// open the Linux device
void i2cOpen()
{
    g_i2c_fd = open("/dev/i2c-1", O_RDWR);
    if (g_i2c_fd < 0)
    {
        perror("i2cOpen");
        exit(1);
    }
}

// close the Linux device
void i2cClose()
{
    close(g_i2c_fd);
}

// set the I2C slave address for all subsequent I2C device transfers
void i2cSetAddress(int address)
{
    if (ioctl(g_i2c_fd, I2C_SLAVE, address) < 0)
    {
        perror("i2cSetAddress");
        exit(1);
    }
}

/*!
 * @brief           Write operation in either Wire or SPI
 *
 * param[in]        reg_addr        register address
 * param[in]        reg_data_ptr    pointer to the data to be written
 * param[in]        data_len        number of bytes to be written
 * param[in]        intf_ptr        interface pointer
 *
 * @return          result of the bus communication function
 */
int8_t bus_write(uint8_t reg_addr, const uint8_t *reg_data_ptr, uint32_t data_len, void *intf_ptr)
{
    int8_t rslt = 0; /* Return 0 for Success, non-zero for failure */

    uint8_t reg[16];
    reg[0] = reg_addr;
    int i;

    for (i = 1; i < data_len + 1; i++)
        reg[i] = reg_data_ptr[i - 1];

    if (write(g_i2c_fd, reg, data_len + 1) != data_len + 1)
    {
        perror("user_i2c_write");
        rslt = 1;
        exit(1);
    }

    return rslt;
}

/*!
 * @brief           Read operation in either Wire or SPI
 *
 * param[in]        reg_addr        register address
 * param[out]       reg_data_ptr    pointer to the memory to be used to store the read data
 * param[in]        data_len        number of bytes to be read
 * param[in]        intf_ptr        interface pointer
 *
 * @return          result of the bus communication function
 */
int8_t bus_read(uint8_t reg_addr, uint8_t *reg_data_ptr, uint32_t data_len, void *intf_ptr)
{
    int8_t rslt = 0; /* Return 0 for Success, non-zero for failure */

    uint8_t reg[1];
    reg[0] = reg_addr;

    if (write(g_i2c_fd, reg, 1) != 1)
    {
        perror("user_i2c_read_reg");
        rslt = 1;
    }

    if (read(g_i2c_fd, reg_data_ptr, data_len) != data_len)
    {
        perror("user_i2c_read_data");
        rslt = 1;
    }

    return rslt;
}

/*!
 * @brief           System specific implementation of sleep function
 *
 * @param[in]       t_us     Time in microseconds
 * @param[in]       intf_ptr Pointer to the interface descriptor
 *
 * @return          none
 */
void sleep_n(uint32_t t_us, void *intf_ptr)
{
    struct timespec ts;
    ts.tv_sec = 0;
    ts.tv_nsec = t_us * 1000;
    nanosleep(&ts, NULL);
}

/*!
 * @brief           Capture the system time in microseconds
 *
 * @return          system_current_time    current system timestamp in microseconds
 */
int64_t get_timestamp_us()
{
    struct timeval tp;
    gettimeofday(&tp, NULL);

    int64_t timeMs = tp.tv_sec * 1000000 + tp.tv_usec;

    if (lastTimeMS > timeMs) /* An overflow occurred */
    {
        overflowCounter++;
    }
    lastTimeMS = timeMs;

    return timeMs + (overflowCounter * INT64_C(0xFFFFFFFF));
}

/*!
 * @brief           Handling of the ready outputs
 *
 * @param[in]       outputs                 output_t structure
 * @param[in]       bsec_status             value returned by the bsec_do_steps() call
 *
 * @return          none
 */
void output_ready(output_t *outputs, bsec_library_return_t bsec_status)
{
    printf("{\"IAQ_Accuracy\": \"%d\",\"IAQ\":\"%.2f\"", outputs->iaq_accuracy, outputs->iaq);
    printf(",\"Temperature\": \"%.2f\",\"Humidity\": \"%.2f\",\"Pressure\": \"%.2f\"", outputs->temperature,
           outputs->humidity, outputs->raw_pressure);
    printf(",\"Gas\": \"%.2f\"", outputs->gas_percentage);
    printf(",\"Status\": \"%d\"", bsec_status);
    printf(",\"Static_IAQ\": \"%.2f\"", outputs->static_iaq);
    printf(",\"eCO2\": \"%.15f\"", outputs->co2_equivalent);
    printf(",\"bVOCe\": \"%.25f\"}", outputs->breath_voc_equivalent);
    printf("\r\n");
    fflush(stdout);
}

uint32_t binary_load(uint8_t *b_buffer, uint32_t n_buffer, char *filename, uint32_t offset)
{
    int32_t copied_bytes = 0;
    int8_t rslt = 0;

    struct stat fileinfo;
    rslt = stat(filename, &fileinfo);
    if (rslt != 0)
    {
        fprintf(stderr, "stat'ing binary file %s: ", filename);
        perror("");
        return 0;
    }

    uint32_t filesize = fileinfo.st_size - offset;

    if (filesize > n_buffer)
    {
        fprintf(stderr, "%s: %d > %d\n", "binary data bigger than buffer", filesize, n_buffer);
        return 0;
    }
    else
    {
        FILE *file_ptr;
        file_ptr = fopen(filename, "rb");
        if (!file_ptr)
        {
            perror("fopen");
            return 0;
        }
        fseek(file_ptr, offset, SEEK_SET);
        copied_bytes = fread(b_buffer, sizeof(char), filesize, file_ptr);
        if (copied_bytes == 0)
        {
            fprintf(stderr, "%s empty\n", filename);
        }
        fclose(file_ptr);
        return copied_bytes;
    }
}

/*!
 * @brief           Load previous library state from non-volatile memory
 *
 * @param[in,out]   state_buffer    buffer to hold the loaded state string
 * @param[in]       n_buffer        size of the allocated state buffer
 *
 * @return          number of bytes copied to state_buffer
 */
uint32_t state_load(uint8_t *state_buffer, uint32_t n_buffer)
{
    int32_t rslt = 0;
    rslt = binary_load(state_buffer, n_buffer, filename_state, 0);
    return rslt;
}

/*!
 * @brief           Save library state to non-volatile memory
 *
 * @param[in]       state_buffer    buffer holding the state to be stored
 * @param[in]       length          length of the state string to be stored
 *
 * @return          none
 */
void state_save(const uint8_t *state_buffer, uint32_t length)
{
    FILE *state_w_ptr;
    state_w_ptr = fopen(filename_state, "wb");
    fwrite(state_buffer, length, 1, state_w_ptr);
    fclose(state_w_ptr);
}

/*!
 * @brief           Load library config from non-volatile memory
 *
 * @param[in,out]   config_buffer    buffer to hold the loaded state string
 * @param[in]       n_buffer        size of the allocated state buffer
 *
 * @return          number of bytes copied to config_buffer
 */
uint32_t config_load(uint8_t *config_buffer, uint32_t n_buffer)
{
    int32_t rslt = 0;
    /*
     * Provided config file is 4 bytes larger than buffer.
     * Apparently skipping the first 4 bytes works fine.
     *
     */
    rslt = binary_load(config_buffer, n_buffer, filename_config, 4);
    return rslt;
}

/*!
 * @brief       Main function which configures BSEC library and then reads and processes the data from sensor based
 *              on timer ticks
 *
 * @return      result of the processing
 */
void setup()
{
    i2cOpen();
    i2cSetAddress(i2c_address);

    struct bme68x_dev bme_dev[NUM_OF_SENS];
    return_values_init ret;

    for (uint8_t i = 0; i < NUM_OF_SENS; i++)
    {

        memset(&bme_dev[i], 0, sizeof(bme_dev[i]));
        bme_dev[i].intf = BME68X_I2C_INTF;
        bme_dev[i].read = bus_read;
        bme_dev[i].write = bus_write;
        bme_dev[i].delay_us = sleep_n;

        /* Assigning a chunk of memory block to the bsecInstance */
        allocateMemory(bsec_mem_block[i], i);

        /* Call to the function which initializes the BSEC library
         * Switch on low-power mode and provide no temperature offset */
        ret = bsec_iot_init(BSEC_SAMPLE_RATE_LP, 0.0f, bus_write, bus_read, sleep_n, state_load, config_load,
                            bme_dev[i], i);

        if (ret.bme68x_status)
        {
            /* Could not initialize BME68x */
            printf("ERROR while initializing BME68x: %i", +ret.bme68x_status);
            return;
        }
        else if (ret.bsec_status < BSEC_OK)
        {
            printf("\nERROR while initializing BSEC library: %d\n", ret.bsec_status);
            return;
        }
        else if (ret.bsec_status > BSEC_OK)
        {
            printf("\nWARNING while initializing BSEC library: %d\n", ret.bsec_status);
        }
    }

    bsec_version_t version;
    bsec_get_version_m(bsecInstance, &version);
    printf("BSEC version: %d.%d.%d.%d\n", version.major, version.minor, version.major_bugfix, version.minor_bugfix);
}

void loop()
{
    /* Call to endless loop function which reads and processes data based on sensor settings */
    /* State is saved every 10.000 samples, which means every 10.000 * 3 secs = 500 minutes  */
    bsec_iot_loop(sleep_n, get_timestamp_us, output_ready, state_save, 10000);
}

int main()
{
    setup();
    loop();
}
