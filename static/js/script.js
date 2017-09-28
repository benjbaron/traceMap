mapboxgl.accessToken = 'pk.eyJ1IjoiYmVuamJhcm9uIiwiYSI6InItaHotTkkifQ.Im25SdEu7d8FNUSXKq8orA';

var map = new mapboxgl.Map({
    container: 'map',
    style: 'mapbox://styles/mapbox/light-v9',
    center: [-96, 37.8],
    zoom: 3
});

var listingEl = document.getElementById('layer-listing');
var availableTraces = {}
var availableTracesUrl = '/gettraceslist';
var layersShown = new Set();
var legendShown = null;

var begTime   = 0
var startTime = 0
var endTime   = 0

function getTimeBounds(features, prop) {
  var minBound = 1e10;
  var maxBound = 0;

  features.forEach(function(e) {
    if(minBound > e.properties[prop])
      minBound = e.properties[prop];

    if(maxBound < e.properties[prop])
      maxBound = e.properties[prop];
  });

  return [minBound, maxBound];
}

function renderLayerListings(traceIds) {
  // Clear any existing listings
  if (traceIds.length) {
    traceIds.forEach(function(traceId) {
      var divId = 'layer-'+traceId;
      var elExists = document.getElementById(divId);
      if(elExists !== null) {
        return;
      }

      var traceName = availableTraces[traceId].trace_id + 
        " (" + availableTraces[traceId].user_id + ") - " +
        availableTraces[traceId].type;
      var div = document.createElement('div');
      div.setAttribute('id', divId);

      var item = document.createElement('span');
      var button = document.createElement('button');
      var checkbox = document.createElement('input');
      var handle = document.createElement('i');
      handle.setAttribute('class', 'fa fa-bars handle');
      handle.setAttribute('aria-hidden', 'true');

      checkbox.setAttribute('type', 'checkbox');
      checkbox.setAttribute('name', 'show-layer');
      checkbox.setAttribute('value', traceId);
      checkbox.defaultChecked = true;
      checkbox.addEventListener('change', function (event) {
        // get the layerId
        var layerId = checkbox.value;
        if (checkbox.checked) {
          map.setLayoutProperty(layerId, 'visibility', 'visible');
          map.on('click', layerId, generatePopupHTML);
        } else {
          map.setLayoutProperty(layerId, 'visibility', 'none');
          map.off('click', layerId, generatePopupHTML);
        }
      });
      button.innerHTML = "<span aria-hidden='true'>&times;</span>";
      button.setAttribute('class', 'close');
      button.setAttribute('aria-label', 'Close');
      button.setAttribute('id', 'del-'+traceId);
      button.addEventListener('click', function() {
        var layerId = button.id.match(/del\-(.*)/)[1];
        var sourceId = availableTraces[layerId]["source-id"];
        map.removeLayer(traceId);
        map.removeSource(sourceId);
        map.off('click', traceId, generatePopupHTML);
        listingEl.removeChild(div);
        layersShown.delete(traceId);
        if(legendShown === traceId) {
          legendShown = null;
          $('#layer-modal-panel').toggle('slide');
        }
        if(layersShown.size == 0) {
          $("#timeline-slider").hide();
        }
      });
      item.textContent = traceName;
      item.addEventListener('click', function() {
        if(legendShown === traceId) {
          $('#layer-modal-panel').toggle('slide');
          legendShown = null;
        } else if(legendShown !== null) {
          renderLegend(traceId);
          legendShown = traceId;
        } else {
          renderLegend(traceId);
          $('#layer-modal-panel').toggle('slide');
          legendShown = traceId;
        }
      });

      div.appendChild(handle);
      div.appendChild(checkbox);
      div.appendChild(item);
      div.appendChild(button);
      listingEl.insertBefore(div, listingEl.firstChild);
    });

    $('#layer-listing').sortable({
      handle: '.handle',
      cursor: 'move',
      update: function(event, ui) {
        var data = $(this).sortable('toArray');
        var traceIds = []
        data.forEach(function (layer){
          var layerId = layer.match(/layer\-(.*)/)[1];
          traceIds.push(layerId);
          map.removeLayer(layerId);
        });
        showTraces(traceIds);
      }
    });
  }
}

function renderTraceListing(data) {
  var modalBody = document.getElementById('layerModal-body');

  // remove all children nodes
  // From: https://stackoverflow.com/questions/3955229/remove-all-child-elements-of-a-dom-node-in-javascript
  while (modalBody.firstChild) {
    modalBody.removeChild(modalBody.firstChild);
  }

  for(var traceId in data) {
    if(layersShown.has(traceId)) {
      continue;
    }

    var trace = data[traceId];
    var div = document.createElement('div');
    div.setAttribute('class', 'modal-body-trace');

    var checkbox = document.createElement('input');
    checkbox.setAttribute('type', 'checkbox');
    checkbox.setAttribute('name', 'trace');
    checkbox.setAttribute('value', traceId);
    checkbox.defaultChecked = false;

    var item = document.createElement('span');
    item.textContent = trace.trace_id + " (" + trace.user_id + ") - " + trace.type;
    item.addEventListener('click', function(){
      this.previousSibling.checked = !this.previousSibling.checked;
    });

    div.appendChild(checkbox);
    div.appendChild(item);
    modalBody.insertBefore(div, modalBody.firstChild);
  }

  var p = document.createElement('p');
  p.textContent = "The following "+data.nb_traces+" traces are available to select:";
  modalBody.insertBefore(p, modalBody.firstChild);
}

function renderLegend(traceId) {
  var trace = availableTraces.traces[traceId];
  var panelEl = document.getElementById('layer-modal-panel-content');
  panelEl.textContent = "";

  for(var key in trace.legend) {
    var keyProperty = trace.legend[key]["key-property"];
    var keyTitle  = trace.legend[key]["key-title"];
    
    var keyMinVal = trace.paint[keyProperty]["stops"][0][0];
    var keyMinCol = trace.paint[keyProperty]["stops"][0][1];
    var keyMaxVal = trace.paint[keyProperty]["stops"][1][0];
    var keyMaxCol = trace.paint[keyProperty]["stops"][1][1];

    var divLegend = document.createElement('div');
    divLegend.setAttribute('id', 'legend-'+traceId);
    divLegend.setAttribute('class', 'legend');
  
    var divKey = document.createElement('div');
    divKey.textContent = keyTitle;
    divLegend.appendChild(divKey);

    var divBar = document.createElement('div');
    divBar.setAttribute('class', 'bar');
    
    var divBarItem = document.createElement('div');
    divBarItem.setAttribute('class', 'bar-item');
    divBarItem.setAttribute('style', 'background: linear-gradient(to right, '+keyMinCol+', '+keyMaxCol+')');
    var divBarLeft = document.createElement('div');
    divBarLeft.setAttribute('class', 'bar-text left');
    divBarLeft.textContent = keyMinVal;
    var divBarRight = document.createElement('div');
    divBarRight.setAttribute('class', 'bar-text right');
    divBarRight.textContent = keyMaxVal;
    
    divBar.appendChild(divBarItem);
    divBar.appendChild(divBarLeft); 
    divBar.appendChild(divBarRight);
    divLegend.appendChild(divBar);
    panelEl.appendChild(divLegend);
  }
  
}

// Define a defer function for d3.queue
// https://github.com/d3/d3-queue
function get(value, callback) {
  callback(null, value);
}

function showTraces(traceIds) {
  // doc for d3.queue: https://github.com/d3/d3-queue
  var queue = d3.queue();
  queue.defer(get, traceIds)
  for(var idx in traceIds.reverse()) {
    var traceId = traceIds[idx];
    var trace_id = availableTraces[traceId].trace_id;
    var user_id = availableTraces[traceId].user_id;
    var type = availableTraces[traceId].type;
    var traceUrl = "showtrace?trace_id="+trace_id+"&user_id="+user_id+"&type="+type;
    queue.defer(d3.json, traceUrl);
  }
  queue.awaitAll(renderTraces);
}

function generatePopupHTML(e) {
  var traceId = e.features[0].layer.id;
  var popup = availableTraces[traceId]["popup"];
  var s = "";
  for(var attribute in popup.attributes) {
    var type = popup.attributes[attribute];
    var value = "";
    if(type === "dateMS") {
      value = moment.unix(e.features[0].properties[attribute]/1000).format("D/M/YY H:mm:ss")
    } else if(type === "timeMS") {
      value = e.features[0].properties[attribute]/1000+" seconds";
    } else {
      value = e.features[0].properties[attribute];
    }
    s += "<strong>"+attribute+": </strong> "+value+"<br />";
  }
  
  var lnglat = e.lngLat;
  new mapboxgl.Popup()
    .setLngLat(lnglat)
    .setHTML(s)
    .addTo(map);
}

function renderTraces(error, data) {
  if(error) throw error;
  var traceIds = data[0];
  var minTS = 1e20;
  var maxTS = 0;
  data.shift();
  for(var idx in data) {
    var traceId = traceIds[idx];
    var sourceId = availableTraces[traceId]["source-id"];
    var sourceType = availableTraces[traceId]["data-type"];
    var dataSource = data[idx];
    var type = availableTraces[traceId]["type"];
    var paint = availableTraces[traceId]["paint"];
    var layout = availableTraces[traceId]["layout"];
    var start_ts = availableTraces[traceId]["timeline"]['start'];
    var end_ts = availableTraces[traceId]["timeline"]['end'];
    if(minTS > start_ts)
      minTS = start_ts;
    if(maxTS < end_ts)
      maxTS = end_ts;

    if(typeof map.getSource(sourceId) === "undefined") {
      map.addSource(sourceId, {
        'type': sourceType,
        'data': dataSource
      });
    }

    if(typeof map.getLayer(traceId) === "undefined") {
      map.addLayer({
        "id": traceId,
        "type": type,
        "source": sourceId,
        "paint": paint,
        "layout": layout
      });

      map.on('click', traceId, generatePopupHTML);
    }

    layersShown.add(traceId);
  }
  renderLayerListings(traceIds);

  startTime = 0;
  endTime = maxTS - minTS;

  $("#timeline-slider").show();
  $("#slider").ionRangeSlider({
    hide_min_max: true,
    keyboard: true,
    min: startTime,
    max: endTime,
    from: startTime,
    to: endTime,
    type: 'double',
    step: 1000,
    grid: true,
    prettify: function (num) {
      var t = moment.unix((minTS+num)/1000).format("D/M/YY H:mm:ss");
      // t += "<br/>";
      // t += moment.unix((begTime+num)/1000).format("H:mm:ss");
      return t;
    },
    onFinish: function (d) {
      // filter the map data
      var from  = minTS + d.from;
      var to    = minTS + d.to;

      var layersShownArr = Array.from(layersShown);
      for(var idx in layersShownArr) {
        var layerId = layersShownArr[idx];
        map.setFilter(layerId, [
          "all",
          [">=", "ts_start", from],
          ["<=", "ts_start", to]
        ]);
      }
    }
  });
}

function init() {    
  map.addControl(new mapboxgl.NavigationControl());
  
  var traceAdd = document.getElementById("layerModal-button");
  traceAdd.addEventListener('click', function() {
    $('#layerModal #layerModal-title').text("Traces available");
    d3.json(availableTracesUrl, function(error, data) {
      if(error) throw error;
      availableTraces = data;
      renderTraceListing(data);
    });
    $('#layerModal').modal("show");
  });

  var traceModalSave = document.getElementById("layerModal-save");
  traceModalSave.addEventListener('click', function() {
    var tracesIdsToShow = []
    $("#layerModal-body input:checkbox:checked").each(function(){
      tracesIdsToShow.push($(this).val());
    });
    showTraces(tracesIdsToShow);
    $('#layerModal').modal("hide");
  });
}

map.on('load', init);

