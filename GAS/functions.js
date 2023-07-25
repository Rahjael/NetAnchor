/**
 * 
 *  This is a public API hosted in a Google Drive environment.
 * 
 *  It serves as a collector for home hosted servers under dynamic IPs,
 *  providing a way to have mobile apps and web services being able to access those
 *  servers without having to rely on third party services like DynDNS and the like.
 * 
 */




// Mock object given by GPT to understand better what is received with doPost(e)
/*
{
  queryString: null, // Any query string parameters in the URL, or null if there are none
  parameter: {
    // Any URL parameters or POSTed parameters
    // Both appear here regardless of how they were sent
    param1: 'value1',
    param2: 'value2',
  },
  parameters: {
    // Similar to above, but each value is an array of strings
    param1: ['value1'],
    param2: ['value2'],
  },
  contextPath: '', // The part of the URL after the script ID
  contentLength: 36, // The length of the payload data
  postData: {
    length: 36,
    type: 'application/x-www-form-urlencoded', // The MIME type of the payload data
    contents: 'param1=value1&param2=value2', // The raw payload data as a string
    name: 'postData',
    // A JavaScript object parsed from the payload data
    // This is only available if the payload data is of type application/json or application/x-www-form-urlencoded
    getDataAsString: function() { return this.contents; },
    getDataAsBlob: function() { }, // Returns a Blob object representing the payload data
    getDataAsJSONObject: function() { }, // Returns a JavaScript object parsed from the payload data
    setEncoding: function() {  }, // Sets the charset to use when interpreting the payload data
  },
}
*/


SHEET = {
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
        return createResponse(401, 'INVALID AUTHCODE');
      }
      logThisNotice('AUTHORIZATION GRANTED', 'granted');
  
      // Evaluate requestType and act accordingly
      logThisNotice('REQUEST RECEIVED', contents.requestType);
      switch(contents.requestType) {
        case 'UPDATE_IP':
          updateIp(contents.serviceName, contents.ip);
          cleanupService(contents.serviceName);
          return createResponse(200, `Logged new ip for service ${contents.serviceName}: ${contents.ip}`, 'OK');
  
        case 'REQUEST_IP':
          const lastIp = retrieveLastIp(contents.serviceName);
          return createResponse(200, `Last known ip for service ${contents.serviceName}: ${lastIp}`, lastIp);
  
        default:
          logThisNotice('ERROR', `could not understand request: ${contents.requestType}`);
      }
  
      cleanupLogsSheet();
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
  function retrieveLastIp(serviceName) {
    // 1. Get the entire table as 2d array - this is faster than checking every row with single calls
    // 2. Filter the result to only the rows with the serviceName we want
    // 3. Since .filter() preserves order, the record we want is the last item of the filtered array, so we can just .pop() it
    const ip = SHEET.IP_HISTORY.getRange(2, 1, SHEET.IP_HISTORY.getLastRow(), SHEET.IP_HISTORY.getLastColumn()).getValues()
    .filter(row => row[CONFIG.COLUMNS.SERVICE_NAME - 1] === serviceName).pop()[CONFIG.COLUMNS.SERVICE_IP - 1];
  
    return ip;
  }
  
  /**
   * Logs a new ip for serviceName
   * @param {string} serviceName - The service
   * @param {string} ip - The new ip to log
   */
  function updateIp(serviceName, ip) {
    const newRow = [Date.now(), serviceName, ip];
    SHEET.IP_HISTORY.appendRow(newRow);
    logThisNotice('IP UPDATED', `New IP ${ip} logged for service ${serviceName}`);
  }
  
  /**
   * For every service, deletes the oldest IPs exceeding the maximum number
   * allowed for storage.
   * For practical reasons the function takes all the data from the sheet, manipulates it,
   * and then rewrites it in bulk.
   * I think this approach is more efficient than making multiple calls to the same sheet.
   */
  function clearObsoleteIPs() {
    // Take all the data
    const ipHistoryTable = SHEET.IP_HISTORY.getRange(2, 1, SHEET.IP_HISTORY.getLastRow(), SHEET.IP_HISTORY.getLastColumn()).getValues();
  
    // Check from the bottom of the list and keep the last MAX_IP_LOGS_FOR_EVERY_SERVICE
    const seenLabels = {};
    const newIpHistoryTable = []
    for (let i = ipHistoryTable.length - 1; i > 0; i--) {
      const currentLabel = ipHistoryTable[i][CONFIG.COLUMNS.SERVICE_NAME - 1];
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
    newIpHistoryTable.reverse().forEach(row => SHEET.IP_HISTORY.appendRow(row));
    logThisNotice('clearObsoleteIPs', 'Cleared obsolete IPs')
  }
  
  /**
   * Deletes old logs when they are more than CONFIG.MAX_LOGS
   */
  function clearExceedingLogs() {
    const lastRow = CONFIG.LOG_SHEET.getLastRow();
    if(lastRow > CONFIG.MAX_LOGS) {
      CONFIG.LOG_SHEET.deleteRows(1, lastRow - CONFIG.MAX_LOGS);
    }
  }
  
  /**
   * Deletes all the logs in the LOG sheet
   * leaving the header row
   */
  function clearLogs() {
    const lastRow = SHEET.LOG.getLastRow();
    if (lastRow > 1) {
      SHEET.LOG.deleteRows(2, lastRow - 1);
    }
  }
  
  /**
   * Deletes all the logs in the IP_HISTORY sheet
   * leaving the header row
   */
  function clearIPHistory() {
    const lastRow = SHEET.IP_HISTORY.getLastRow();
    if (lastRow > 1) {
      SHEET.IP_HISTORY.deleteRows(2, lastRow - 1);
    }
  }
  
  /**
   * Logs an entire object (for debugging purposes)
   * Structure is [Date in ms, Date readable, objectName, objStringified]
   * @param {string} objectName - The name of the object to log.
   * @param {object} obj - The object or property to log.
   */
  function logThisObject(objectName, obj) {
    SHEET.LOG.appendRow([Date.now(), Date().toString(), objectName, JSON.stringify(obj)]);
  }
  
  /** Appends a new row to the LOG sheet as a [Date in ms, Date readable, eventName, message]
   * @param {string} eventName - The name of the event to log.
   * @param {string} string - The message to log
   */
  function logThisNotice(eventName, message) {
    SHEET.LOG.appendRow([Date.now(), Date().toString(), eventName, message]);
  }
  
  
  
  
  
  