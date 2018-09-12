# GMX_PI_HAT
The GMX PI HAT brings the GMX module interface to the Raspberry PI world, opening this platform to the GMX IoT modules world.
As you can see from the picture with this HAT your Raspberry PI can use two GMX modules.<br/><br/>
<img src="/docs/pihat_3.png"/>
<br/>
<img src="/docs/pihat_1.png"/>
<br/>
<br/>
The HAT simply bring the PI GPIOS over to the GMX connectors and adds a dual IC2 UART interface based on the NXPSC16752 chip.<br/>
The HAT works with the 40 Pins PI extension board - so (very) old versions of the PI won't be compatible.<br/>
Full schematics are coming as well...<br/>

## How to Configure your PI with Raspian
You need to add support for the NXPSX16752 chipset before being able to use the board. This, hopefully, should be quite easy.<br/>
We have been testing the latest Raspian release Stretch ( as of August 2017).
<br/>
As we are using the I2C version of the chip so first of all you need to enable I2C on the PI ( if you haven't yet done it)

```bash
sudo raspi-config
```
* Choose Interfacing options.
* Choose I2C Enable/Disable automatic loading.
* Follow the prompts to set this to load this automatically.
* Reboot the Pi.
<br/>

Then install the I2C utilities
<br/>

```bash
sudo rpi-update
sudo apt-get update 
sudo apt-get install -y i2c-tools
```
<br/>
and let's test if you can identify the GMX PI HAT.
<br/>

```bash
sudo i2cdetect -y 1
```
<br/>

You should see a device at address 0x4D.

<br/>
Now let's add the kernel support for the SC16IS752.<br/>
<br/>

Edit the module files
<br/>
```bash
sudo nano /etc/modules 
```
Add at the bottom the line

```bash
sc16is7xx
```

You should have something like this:
```bash
# /etc/modules: kernel modules to load at boot time.
#
# This file contains the names of kernel modules that should be loaded
# at boot time, one per line. Lines beginning with "#" are ignored.

i2c-dev
sc16is7xx
```

The we need to create the Device Tree Overlay sc16is752-i2c.dts.<br/> 
By default the SPI version is already present but not the I2C one ( thanks to [MaterWuff](https://www.raspberrypi.org/forums/viewtopic.php?f=107&t=146908&start=25) ) here are the steps.<br/>
<br/>
Create the file<br>
```bash

sudo nano sc16is752-i2c.dts
```

and copy this content:

```bash
/dts-v1/;
/plugin/;

/ {
    compatible = "brcm,bcm2835", "brcm,bcm2836", "brcm,bcm2708", "brcm,bcm2709"; // Depending on your RPi Board Chip
    
    fragment@0 {
        target = <&i2c1>;
        
        frag1: __overlay__ {
            #address-cells = <1>;
            #size-cells = <0>;
            status = "okay";

            sc16is752: serial@4d {
                compatible = "nxp,sc16is752";
                reg = <0x4D>; // i2c address
                clocks = <&sc16is752_clk>;
                interrupt-parent = <&gpio>;
                interrupts = <17 0x2>; //GPIO and falling edge
                gpio-controller;
                #gpio-cells = <0>;
                i2c-max-frequency = <400000>;
                status = "okay";
            };
        };
    };

    fragment@1 {
        target-path = "/";

        __overlay__ {
            sc16is752_clk: sc16is752-clk {
                compatible = "fixed-clock";
                clock-frequency = <1843200>;
                #clock-cells = <0>;
            };
        };
    };

    __overrides__ {
        int_pin = <&sc16is752>,"interrupts:0";
    };
};

```
<br/>
The GMX PI HAT has i2c address at <b>0x4D</b> and interrupt pin GPIO <b>17</b>.<br/>
<br/>

Now we need to create the DTBO overlay file ( and you need kernel > 4.4 - use 'uname -r' to check).<br/>

```bash
dtc -@ -I dts -O dtb -o sc16is752-i2c.dtbo sc16is752-i2c.dts
```

If there is a warning, like this...<br/>
```bash
sc16is752-i2c.dtbo: Warning (unit_address_vs_reg): Node /fragment@0 has a unit name, but no reg property 
```
Its fine..<br/>

and copy it to the overlay folder

```bash
sudo cp sc16is752-i2c.dtbo /boot/overlays/
```

and finally activate in the <b>/boot/config.txt</b>.<br/>
Add the line: dtoverlay=sc16is752-i2c ( usually at the bottom of the file)<br/>
Add the beginning of the config.txt file the 'debug on': dtdebug=on ( once everything works you can remove this)</br>

<br>
Reboot your PI.
<br/>


Let's check if everything works:
```bash
lsmod
```
you should see the file 'sc16is7xx'<br/>
then..<br/>
```bash
sudo vcdbg log msg
```
and you should find the "Loaded overlay 'sc16is752-i2c'" line

and finally...<br/>
```bash
ls –l /dev/ttyS*
```

And you should see the additional UART ports for the 2 GMX modules:
* /dev/ttySC0 
* /dev/ttySC1
<br/>
The HAT is configured and working!

# Pinout RaspberryPI / GMX Slots
Here is the table showing the connection between the RapsberryPI GPIO ports and the GMX Slots.
<img src="docs/gmx_pi_hat_pinout.png">
<br/>
<br/>

# Some example Code

In this repo we will add differnt examples to use our GMX modules.<br>
The first 'basic' example is for the LoRaWAN GMX-LR1 module <b>gmx_lr1.py</b>, this is a first version of the python code to make a LoRaWAN connection.<br/>
The gmx_nbiot.py is an example file to run the GMX-NBIoT module with configuration for Deutsche Telekom network.<br/>
The gmx_catm1.py is an example file to run the GMX-CATM1 module with configuration for Swisscom network.<br/>
<br/>
These examples are still quite rough but they work!<br/>
To make them work you need to install python-serial module:

```bash
 sudo apt-get install python-serial
 ```
<br/>
<br/>
Stay tuned for updates and feel free to change it as you wish, and if you want to contribute you are very welcome!



# Contact

If you want additional info please contat us at [info@gimasi.ch](mailto:info@gimasi.ch)





