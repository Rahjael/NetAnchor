# NetAnchor

Keep track of dynamic IPs for all your connected devices, encrypted and private. 

## How it works

NetAnchor updates the IP table on Google Sheet using App Script, each device is responsible for sending its own IP, the PC you are operating on just reads the up-to-date Sheet.

![visual-explanation](docs/NetAnchor-draw.png)

## Instructions
- Install NetAnchor on the devices you want to track
- Login with Google 
- App Script permissions
- Enjoy!

## Quick Start

### GAS Setup

- Create files in a Google Drive folder:
  - Google Sheet
    - empty sheet called `LOG`
    - empty sheet called `IP_HISTORY`
  - Google Apps Script (refer to the GAS folder)
    - script called `config.gs` (static configurations)
    - script called `functions.gs` (dynamic code)

- GAS
  - in `config.gs` 
    - `SPREADSHEET_ID` will be gathered from the Database sheet from the URL `/d/example_speradsheet_id_random_characters/edit`
    - `AUTHCODE` can be a made up code, this just have to be identical to the one in the `Python/config.json`
  - in `functions.gs` 
    - just paste the content of `GAS/functions.js` file
  - Execute to grant permissions
    - In the first run it will ask for permissions, which of course will have to be accepted in order to make this work. 
  - Deployment (a new deployment will be needed for each GAS code modification, it changes the URL, so keep changes to the minimum)
    - Deploy
    - Web App
    - (name of preference)
    - Access: Anyone
    - Deploy
    - Copy Web App URL
    - Paste it in `Python/config.json`, `GAS_SCRIPT_URL`


## Suggested tools
- ipfy API is used for retrieving the IPs