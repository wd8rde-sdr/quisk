git clone https://github.com/wd8rde-sdr/quisk.git
cd quisk
make quisk
./quisk

Quick start configuring Quisk for the Genesis G59:
   Click config,
      Add New Radio of General Type: "SoftRock USB", and name the new radio: "Genesis G59"
   Click on tab "Genesis G59"
      In the Hardware Tab:
         Hardware file path: <path to genesis-g59/hardware_usb.py>
         Widget file path: <path to genesis-g59/widgets_tx.py>
      Under the Sound tab, configure your sound devices, I use pulse for Radio Sound Output, and Microphone Input. And then alsa hw: devices for I/Q Sample In/Out.

Quisk information from this file is now in docs.html.
