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

var s = document.styleSheets[1];

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
            create_field();
            break;
        case "EVENT_END_TICTACTOE":
            console.log("clearing bord");
            clear_field();
            clear_field();
            clear_field();
            break;
        case "EVENT_ADD_PIECE_TICTACTOE":
            add_piece(data);
            break;
        case "EVENT_RELOAD_SETTINGS_TICTACTOE":
            // TODO: reload settings
            break;
    }
};

function reload_settings(json_data) {
    settings = JSON.parse(json_data);
}

function clear_field() {
    var playfield = document.getElementById("playfield");
    playfield.removeChild(playfield.firstChild);
}

create_field = function () {
    var playfield = document.getElementById("playfield");
    playfield.appendChild(get_field_html());
};

get_field_html = function () {
    var div = document.createElement('table');
    div.innerHTML = table_body_string.trim();
    return div.firstChild;
};

add_piece = function (data) {
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