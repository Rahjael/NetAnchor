/**
 * 
 *  This is a public API hosted in a Google Drive environment.
 * 
 *  It serves as a collector for home hosted servers under dynamic IPs,
 *  providing a way to have mobile apps and web services being able to access those
 *  servers without having to rely on third party services like DynDNS and the like.
 * 
 */



SHEETS = {
  LOG: SpreadsheetApp.openById(CONFIG.SPREADSHEET_ID).getSheetByName(CONFIG.LOG_SHEET_NAME),
  IP_HISTORY: SpreadsheetApp.openById(CONFIG.SPREADSHEET_ID).getSheetByName(CONFIG.IP_HISTORY_SHEET_NAME)
}





function test() {


  Logger.log('test')

  /*
  Logger.log('started')
  clearObsoleteIPs();
  Logger.log('end')
  */


  /*
  const testContentsUPDATE_IP = {
    authCode: 'abcd',
    serviceName: 'blablabla',
    currentIp: '151.26.154.189'
  };
  const testEvent = {
    postData: {
      contents: JSON.stringify(testContentsUPDATE_IP)
    }
  };
  Logger.log(testEvent)
  doPost(testEvent);
  */
}


function doPost(e) {
  /**
   * How the event object is structured https://developers.google.com/apps-script/guides/web
   * 
   * After many trials and errors I think the important points to take home are the following:
   * 
   * 1. 'e' is an object provided by the server when doPost() is triggered. It is a JS object.
   * 
   * 2. The problem arises with the 'contents' property (e.postData.contents), which is sent by the client
   * during the POST request and is actually received as a JSON string, so it must be JSON.parse()'d.
   * 
   * So, in a nutshell:
   * - treat 'e' the JS object which it is.
   * - parse 'e.postData.contents' before trying to access the data it contains.
   */
  
  try {
    logThisObject('POST received:', e);
    const contents = JSON.parse(e.postData.contents);
    logThisObject('CONTENTS', contents);

    // This is just a rudimentary security filter
    if(contents.authCode != CONFIG.AUTHCODE) {
      logThisNotice('AUTHORIZATION DENIED', 'denied');
      return createResponse(401, 'INVALID AUTHCODE');
    }
    logThisNotice('AUTHORIZATION GRANTED', 'granted');

    // Evaluate requestType and act accordingly
    logThisNotice('REQUEST RECEIVED', contents.requestType);
    switch(contents.requestType) {
      case 'UPDATE_IP':
        appendIP(contents.serviceName, contents.ip);
        clearExceedingLogs();
        clearObsoleteIPs();
        return createResponse(200, `Logged new ip for service ${contents.serviceName}: ${contents.ip}`, 'OK');

      case 'REQUEST_IP':
        const lastIp = retrieveLastIP(contents.serviceName);
        return createResponse(200, `Last known ip for service ${contents.serviceName}: ${lastIp}`, lastIp);

      case 'REQUEST_NETWORK':
        const network = retrieveNetwork();
        return createResponse(200, `Currently known network`, network);

      default:
        logThisNotice('ERROR', `could not understand request: ${contents.requestType}`);
    }
  }
  catch (error) {
    logThisNotice('ERROR', `Error handling POST request: ${error}`);
    return createResponse(500, 'Server error');
  }
}

function createResponse(status, message, value = null) {
  const package = {
    status: status,
    message: message,
    value: value
  };
  logThisObject('RESPONSE', package);
  return ContentService.createTextOutput(JSON.stringify(package));
}

/**
 * Returns a network: an array of [label, ip] elements. 
 * Each element is a service with its last known ip.
 */
function retrieveNetwork() {
  const ipHistoryTable = SHEETS.IP_HISTORY.getRange(2, 1, SHEETS.IP_HISTORY.getLastRow(), SHEETS.IP_HISTORY.getLastColumn()).getValues();
  const lastIps = {};

  for (let i = ipHistoryTable.length - 1; i >= 0; i--) {
    const currentRow = ipHistoryTable[i];
    const serviceName = currentRow[CONFIG.COLUMNS.SERVICE_NAME - 1];
    const serviceIp = currentRow[CONFIG.COLUMNS.SERVICE_IP - 1];

    // If the service's IP hasn't been set yet, and the current row's IP isn't empty
    if (!lastIps[serviceName] && serviceIp !== "") {
      lastIps[serviceName] = serviceIp;
    }
  }

  // Convert lastIps object to an array of [label, ip] arrays
  const lastIpsArray = [];
  for (let serviceName in lastIps) {
    lastIpsArray.push([serviceName, lastIps[serviceName]]);
  }

  return lastIpsArray;
}

/**
 * We're not using this at this time, but GAS requires
 * doGet(e) to be there for deploying the script as webapp
 */
function doGet(e) {
  logThisObject('GET received:', e);
}

/**
 * Traverses the table from the bottom up and finds the last known ip 
 * for the requested service.
 * 
 *  @param {string} serviceName - The name of the service
 */
function retrieveLastIP(serviceName) {
  // 1. Get the entire table as 2d array - this is faster than checking every row with single calls
  // 2. Filter the result to only the rows with the serviceName we want
  // 3. Since .filter() preserves order, the record we want is the last item of the filtered array, so we can just .pop() it
  const ip = SHEETS.IP_HISTORY.getRange(2, 1, SHEETS.IP_HISTORY.getLastRow(), SHEETS.IP_HISTORY.getLastColumn()).getValues()
  .filter(row => row[CONFIG.COLUMNS.SERVICE_NAME - 1] === serviceName).pop()[CONFIG.COLUMNS.SERVICE_IP - 1];

  return ip;
}

/**
 * Logs a new ip for serviceName
 * @param {string} serviceName - The service
 * @param {string} ip - The new ip to log
 */
function appendIP(serviceName, ip) {
  const newRow = [Date.now(), serviceName, ip];
  SHEETS.IP_HISTORY.appendRow(newRow);
  logThisNotice('IP UPDATED', `New IP ${ip} logged for service ${serviceName}`);
}

/**
 * For every service, deletes the oldest IPs exceeding the maximum number
 * allowed for storage.
 * For practical reasons the function takes all the data from the sheet, manipulates it,
 * and then rewrites it in bulk.
 * I think this approach is more efficient than making multiple calls to the same SHEETS.
 */
function clearObsoleteIPs() {
  // Take all the data
  const ipHistoryTable = SHEETS.IP_HISTORY.getRange(2, 1, SHEETS.IP_HISTORY.getLastRow(), SHEETS.IP_HISTORY.getLastColumn()).getValues();

  // Check from the bottom of the list and keep the last MAX_IP_LOGS_FOR_EVERY_SERVICE
  const seenLabels = {};
  const newIpHistoryTable = []
  for (let i = ipHistoryTable.length - 1; i >= 0; i--) {
    const currentLabel = ipHistoryTable[i][CONFIG.COLUMNS.SERVICE_NAME - 1];
    Logger.log(seenLabels[currentLabel])
    if (seenLabels[currentLabel]) {
      // Skip if already gotten to max IP to store
      if (seenLabels[currentLabel] >= CONFIG.MAX_IP_LOGS_FOR_EVERY_SERVICE) continue;
      seenLabels[currentLabel] += 1 // Add 1 otherwise
    }
    else seenLabels[currentLabel] = 1 // Set it to 1 if first time we see this label
    newIpHistoryTable.push(ipHistoryTable[i]);
  }

  clearIPHistory();

  // Add back the filtered results
  newIpHistoryTable.reverse()

  if (newIpHistoryTable.length > 0) {
    SHEETS.IP_HISTORY.getRange(2, 1, newIpHistoryTable.length, newIpHistoryTable[0].length).setValues(newIpHistoryTable);
  }

  logThisNotice('clearObsoleteIPs', 'Cleared obsolete IPs')
}

/**
 * Deletes old logs when they are more than CONFIG.MAX_LOGS
 */
function clearExceedingLogs() {
  const lastRow = SHEETS.LOG.getLastRow();
  if(lastRow > CONFIG.MAX_LOGS) {
    SHEETS.LOG.deleteRows(1, lastRow - CONFIG.MAX_LOGS);
  }
}

/**
 * Deletes all the logs in the LOG sheet
 * leaving the header row
 */
function clearLogs() {
  const lastRow = SHEETS.LOG.getLastRow();
  if (lastRow > 1) {
    SHEETS.LOG.deleteRows(2, lastRow - 1);
  }
}

/**
 * Deletes all the logs in the IP_HISTORY sheet
 * leaving the header row
 */
function clearIPHistory() {
  const lastRow =SHEETS.IP_HISTORY.getLastRow();
  if (lastRow > 1) {
    SHEETS.IP_HISTORY.deleteRows(2, lastRow - 1);
  }
}

/**
 * Logs an entire object (for debugging purposes)
 * Structure is [Date in ms, Date readable, objectName, objStringified]
 * @param {string} objectName - The name of the object to log.
 * @param {object} obj - The object or property to log.
 */
function logThisObject(objectName, obj) {
  SHEETS.LOG.appendRow([Date.now(), Date().toString(), objectName, JSON.stringify(obj)]);
}

/** Appends a new row to the LOG sheet as a [Date in ms, Date readable, eventName, message]
 * @param {string} eventName - The name of the event to log.
 * @param {string} string - The message to log
 */
function logThisNotice(eventName, message) {
  SHEETS.LOG.appendRow([Date.now(), Date().toString(), eventName, message]);
}





