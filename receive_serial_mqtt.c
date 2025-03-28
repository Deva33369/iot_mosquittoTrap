#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>      // File control definitions
#include <errno.h>      // Error number definitions
#include <termios.h>    // POSIX terminal control definitions
#include <unistd.h>     // UNIX standard function definitions
#include <MQTTClient.h>  

#define BROKER_ADDRESS "ssl://460dcdee90384eea9518b5463994b160.s1.eu.hivemq.cloud:8883"
#define CLIENT_ID "RaspberryPi_Serial_Publisher"
#define USERNAME "deva33369"
#define PASSWORD "Dinesh0507"
#define TOPIC "sensor"
#define QOS 1
#define INTERVAL 5 

// Function to publish message to MQTT
void publish_message(MQTTClient client, const char *payload) {
    MQTTClient_message pubmsg = MQTTClient_message_initializer;
    pubmsg.payload = (void*)payload;
    pubmsg.payloadlen = strlen(payload);
    pubmsg.qos = QOS;
    pubmsg.retained = 0;

    MQTTClient_deliveryToken token;
    MQTTClient_publishMessage(client, TOPIC, &pubmsg, &token);
    MQTTClient_waitForCompletion(client, token, 1000);

    printf("📤 Published: %s\n", payload);
}

// Function to open and configure serial port
int open_serial_port(const char *port) {
    int serial_fd = open(port, O_RDWR | O_NOCTTY | O_NDELAY);
    if (serial_fd == -1) {
        perror("Error opening serial port");
        return -1;
    } else {
        printf("Serial port opened successfully: %s\n", port);
    }

    struct termios tty;
    memset(&tty, 0, sizeof(tty));
    if (tcgetattr(serial_fd, &tty) != 0) {
        perror("Error getting serial port attributes");
        close(serial_fd);
        return -1;
    }

    // Set baud rate
    cfsetospeed(&tty, B9600);
    cfsetispeed(&tty, B9600);

    // Set other serial port settings
    tty.c_cflag &= ~PARENB;  // No parity
    tty.c_cflag &= ~CSTOPB;  // 1 stop bit
    tty.c_cflag &= ~CSIZE;   // Clear data size bits
    tty.c_cflag |= CS8;      // 8 data bits
    tty.c_cflag &= ~CRTSCTS; // No hardware flow control
    tty.c_cflag |= CREAD | CLOCAL; // Enable receiver, ignore modem control lines

    tty.c_lflag &= ~ICANON;  // Disable canonical mode
    tty.c_lflag &= ~ECHO;    // Disable echo
    tty.c_lflag &= ~ECHOE;   // Disable erasure
    tty.c_lflag &= ~ECHONL;  // Disable new-line echo
    tty.c_lflag &= ~ISIG;    // Disable interpretation of INTR, QUIT, and SUSP

    tty.c_iflag &= ~(IXON | IXOFF | IXANY); // Disable software flow control
    tty.c_iflag &= ~(IGNBRK | BRKINT | PARMRK | ISTRIP | INLCR | IGNCR | ICRNL);

    tty.c_oflag &= ~OPOST; // Disable special handling of output
    tty.c_oflag &= ~ONLCR; // Disable conversion of newline to carriage return/line feed

    tty.c_cc[VMIN] = 0;  // Non-blocking read
    tty.c_cc[VTIME] = 10; // Read timeout in tenths of a second

    // Apply the settings
    if (tcsetattr(serial_fd, TCSANOW, &tty) != 0) {
        perror("Error setting serial port attributes");
        close(serial_fd);
        return -1;
    }

    return serial_fd;
}

int main() {
    // MQTT Client setup
    MQTTClient client;
    MQTTClient_create(&client, BROKER_ADDRESS, CLIENT_ID, MQTTCLIENT_PERSISTENCE_NONE, NULL);

    MQTTClient_connectOptions conn_opts = MQTTClient_connectOptions_initializer;
    conn_opts.username = USERNAME;
    conn_opts.password = PASSWORD;

    MQTTClient_SSLOptions ssl_opts = MQTTClient_SSLOptions_initializer;
    conn_opts.ssl = &ssl_opts;

    if (MQTTClient_connect(client, &conn_opts) != MQTTCLIENT_SUCCESS) {
        printf("❌ Failed to connect to MQTT broker\n");
        return -1;
    }
    printf("✅ Connected to MQTT Broker\n");

    // Open serial port
    const char *port = "/dev/serial0";
    int serial_fd = open_serial_port(port);
    if (serial_fd == -1) {
        return -1;
    }

    // Buffer to store incoming data
    char buffer[256];
    memset(buffer, 0, sizeof(buffer));

    while (1) {
        // Read data from the serial port
        int n = read(serial_fd, buffer, sizeof(buffer) - 1);

        if (n > 0) {
            // Null-terminate the string
            buffer[n] = '\0';
            printf("Received data: %s\n", buffer);

            // Publish the data to MQTT
            publish_message(client, buffer);
        } else if (n == 0) {
            // No data available, nothing to read
        } else {
            // Error reading from serial port
            if (errno != EAGAIN && errno != EWOULDBLOCK) {
                perror("Error reading from serial port");
                break;
            }
        }

        // Clear the buffer
        memset(buffer, 0, sizeof(buffer));

        // Add a small delay to avoid flooding the terminal
        usleep(100000); // 100ms delay
    }

    // Close the serial port and MQTT client
    close(serial_fd);
    MQTTClient_disconnect(client, 1000);
    MQTTClient_destroy(&client);
    printf("🔌 Disconnected from MQTT Broker\n");

    return 0;
}

