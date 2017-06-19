

int WriteData(const unsigned char * data, unsigned long length, const SSP_PORT port);

void SetupSSPPort(const SSP_PORT port);

int BytesInBuffer(SSP_PORT port);

int ReadData(const SSP_PORT port, unsigned char * buffer, unsigned long bytes_to_read);

void SetBaud(const SSP_PORT port, const unsigned long baud);

int TransmitComplete(SSP_PORT port);
