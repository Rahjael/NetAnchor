# NetAnchor

Keep track of dynamic IPs for all your connected devices, encrypted and private. 

## How it works

NetAnchor updates the IP table on Google Sheet using App Script, each device is responsible for sending its own IP, the PC you are operating on just reads the up-to-date Sheet.

![visual-explanation](docs/NetAnchor-draw.png)

## Overview
- Install NetAnchor on the devices you want to track
- Login with Google 
- App Script permissions & Sheets
- Enjoy!

---

## Quick Start

### GAS Setup

- **Google Drive dedicated folder**:
  - Google Sheet
    - empty sheet called `LOG`
    - empty sheet called `IP_HISTORY`
  - Google Apps Script (refer to the GAS folder)
    - script called `config.gs` (static configurations)
    - script called `functions.gs` (dynamic code)

- **GAS**
  - in `config.gs` 
    - `SPREADSHEET_ID` will be gathered from the Database sheet from the URL `/d/example_spreadsheet_id_random_characters/edit`
    - `AUTHCODE` can be a made up code, this just have to be identical to the one in the `Python/config.json`
  - in `functions.gs` 
    - just paste the content of `GAS/functions.js` file

  - **Execute** on *Apps Script* to grant permissions
    - grant permissions
  - **Deployment** on Apps Script
    - Click *Deploy* button (upper right corner)
    - Choose *Web App* and choose any name you like
    - *Access: Anyone* (read below)
    - *Deploy* the App
    - *Copy* Web App URL
    - *Paste* it in `Python/config.json`, `GAS_SCRIPT_URL`

    **Note**: the code URL is public, even if very hard to find being random numbers, but there is no response and no data is sent.

- ***Run...***

### Run `main.py`

- Running `main.py` should now populate the Google Sheet with data
- The data will be accessible through the UI, but you can also access it directly on the Google Sheet

---

## Roadmap

- [x] Working with console logs
- [x] Basic UI
  - [x] Custom configs through UI settings
  - [ ] Implement Logger
- [ ] "Installation package" for GAS. Try to make it as simple as possible to set things up
- [ ] "Doomsday recovery" for GAS. From a button in the Python UI, be able to reset the Sheet's structure in case the user messes it up manually on Google Drive
- [ ] Encryption fix
- [ ] Google Marketplace Add-On to streamline the installation process

## Suggested Tools
- [TightVNC](https://www.tightvnc.com/download.html) for remote access
- [ipfy API](https://www.ipify.org/) is used for retrieving the IPs




## Changelog

- 2023/07/? - (TODO) Release v0.1.0 (beta)