//--------------------------
// Variables
//--------------------------
var serviceUrl = "ws://127.0.0.1:3337/streamlabs";
var socket = new ReconnectingWebSocket(serviceUrl);
socket.maxReconnectInterval = 5000;
socket.reconnectDecay = 1.1;
socket.timeoutInterval = 1000;
var table_body_string = "<tbody>" +
    "<tr><td id='0 0'></td><td id='0 1'></td><td id='0 2'></td></tr>" +
    "<tr><td id='1 0'></td><td id='1 1'></td><td id='1 2'></td></tr>" +
    "<tr><td id='2 0'></td><td id='2 1'></td><td id='2 2'></td></tr>" +
    "</tbody>";

var s = document.styleSheets[0];
window.onload = updateCss;

function changeStylesheetRule(stylesheet, selector, property, value) {
	selector = selector.toLowerCase();
	property = property.toLowerCase();
	value = value.toLowerCase();

	for(var i = 0; i < stylesheet.cssRules.length; i++) {
		var rule = stylesheet.cssRules[i];
		if(rule.selectorText === selector) {
			rule.style[property] = value;
			return;
		}
	}

	stylesheet.insertRule(selector + " { " + property + ": " + value + "; }", 0);
}

//--------------------------
// Open Event
//--------------------------
socket.onopen = function () {
    // TODO: read in ../tictactoeSettings.js
    // Format your Auth info
    var auth = {
        author: "mi_thom + mathiasAC",
        website: "https://www.twitch.tv/mi_thom",
        api_key: API_Key, //this is defined by right click insert api key
        events: [
            "EVENT_START_TICTACTOE",
            "EVENT_END_TICTACTOE",
            "EVENT_ADD_PIECE_TICTACTOE",
            "EVENT_RELOAD_SETTINGS_TICTACTOE"
        ]
    };
    socket.send(JSON.stringify(auth));
};

//--------------------------
// Error Event
//--------------------------
socket.onerror = function (error) {
    console.log("Error: " + error)
};

//--------------------------
// Message Event
//--------------------------
socket.onmessage = function (message) {
    var data = JSON.parse(message.data);
    switch (data["event"]) {
        case "EVENT_START_TICTACTOE":
            clearField();
            createField();
            break;
        case "EVENT_END_TICTACTOE":
            console.log("clearing bord");
            clearField();
            clearField();
            clearField();
            break;
        case "EVENT_ADD_PIECE_TICTACTOE":
            addPiece(data);
            break;
        case "EVENT_RELOAD_SETTINGS_TICTACTOE":
            reloadSettings(data["data"]);
            break;
    }
};

function reloadSettings(json_data) {
    settings = JSON.parse(json_data);
    updateCss()
}

function updateCss() {
    changeStylesheetRule(s, "td", "border-color", settings["border_color"]);
    changeStylesheetRule(s, "td", "background-color", settings["field_color"]);
    changeStylesheetRule(s, "td", "border-width", settings["border_thickness"]+"px");
}

function clearField() {
    var playfield = document.getElementById("playfield");
    if(playfield.firstChild != null){
        playfield.removeChild(playfield.firstChild);
    }
}

createField = function () {
    clearField();
    var playfield = document.getElementById("playfield");
    playfield.appendChild(getFieldHtml());
};

getFieldHtml = function () {
    var div = document.createElement('table');
    div.innerHTML = table_body_string.trim();
    return div.firstChild;
};

addPiece = function (data) {
    data = data["data"];
    data = JSON.parse(data);
    var id = String(data["row"]) + " " + String(data["column"]);
    var td = document.getElementById(id);
    var img = document.createElement("img");
    if(data["player"] === 1){
        img.setAttribute("src", "cross.png");
    }else {
        img.setAttribute("src", "circle.png");
    }
    img.setAttribute("height", "100%");
    img.setAttribute("width", "100%");
    td.appendChild(img);
};

//--------------------------
// Close Event
//--------------------------
socket.onclose = function () {
    console.log("Connection closed")
};