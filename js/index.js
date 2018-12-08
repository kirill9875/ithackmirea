/*--------------Построение карты---------------*/
ymaps.ready(init);
var myMap;
var height = document.documentElement.clientHeight / 4;
var coord_mas = [];
var prev_ts = 0;

function init() {
    myMap = new ymaps.Map('map', {
        zoom: 16,
        center: [55.670110741725935, 37.480677775101185],
        controls: ['geolocationControl']
    });

    myMap.controls.add('zoomControl', {
        position: {
            top: height,
            right: 10
        }
    });
    get_coords();
    //    show_result(55.67, 37.48)
}

function get_coords() {
    setInterval(function () {

        delete_prev();

        var xmlhttp = new XMLHttpRequest();

        var id = "96bcc8a85c394cb4a8858eef1af65fae"

        var call = "https://api.artik.cloud/v1.1/messages/last?count=1&fieldPresence=lat&sdids=" + id;

        xmlhttp.open('GET', call, false);

        xmlhttp.setRequestHeader("Content-Type", "application/json");

        xmlhttp.setRequestHeader("Authorization", "Bearer 191b9167e18d451f8cb80a19214c9164");

        xmlhttp.onreadystatechange = function () {

            if (xmlhttp.status == 200) {
                var prsd = JSON.parse(xmlhttp.responseText);
                //              alert(xmlhttp.responseText);
                var lat = prsd.data[0].data.lat;
                var long = prsd.data[0].data.long;

                var ts = prsd.data[0].ts;
                var sec_ts = ts - prev_ts;
                if (prev_ts == 0)
                    sec_ts = 0;
                prev_ts = ts;

                coord_mas.push([lat, long]);
                show_result(lat, long, sec_ts);
            }
        };

        xmlhttp.send(null);

    }, 3000);
}

function show_result(lat, long, sec_ts) {
    myMap.geoObjects.add(new ymaps.Placemark([lat, long], {
        // Описание геометрии.
        geometry: {
            type: "Point",
        }
    }, {
        preset: "islands#circleIcon",
        iconColor: '#FF0000'
    }));
    var myPolyline = new ymaps.Polyline(
        coord_mas, {}, {
            strokeColor: '#FF0000',
            strokeWidth: 4,
        }
    );
    myMap.geoObjects.add(myPolyline);
    //    speed(sec_ts);
}

function delete_prev() {
    myMap.geoObjects.removeAll();
}

function speed(sec_ts) {
    if (sec_ts == 0) {
        return;
    }
    var length = coord_mas.length - 1;
    if (length == 0) return;
    var deltaX = coord_mas[length][0] - coord_mas[length - 1][0];
    var deltaY = coord_mas[length][1] - coord_mas[length - 1][1];
    deltaX = deltaX * 62.77;
    deltaY = deltaY * 111.111;
    var vector = Math.sqrt(Math.pow(deltaX, 2) + Math.pow(deltaY, 2));
    var spd = vector / sec_ts;
    document.getElementById("speed").innerHTML = spd;
}
