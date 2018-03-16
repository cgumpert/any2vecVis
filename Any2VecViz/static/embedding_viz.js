var labels_visible = false;

var colorScale = d3.scaleOrdinal(d3['schemeCategory10']);
var currentColor = 0;

function toggleLabels() {
	var new_state = labels_visible ? 'hidden' : 'visible';
	d3.selectAll('.label').style('visibility', new_state);
	labels_visible = !labels_visible;
}

function draw_embedding(
	data,
	xmin,
	xmax,
	ymin,
	ymax
) {

// set svg to full screen
var width = window.innerWidth - 22;
var height = window.innerHeight - 22;
var svg = d3.select("svg#map").attr('width', width).attr('height', height);

var zoom = d3.zoom()
    .scaleExtent([1, 100])
    .translateExtent([[-100, -100], [width + 90, height + 100]])
    .on("zoom", zoomed);

var x = d3.scaleLinear()
    .domain([xmin, xmax])
    .range([-1, width + 1]);

var y = d3.scaleLinear()
    .domain([ymin, ymax])
    .range([-1, height + 1]);

var view = svg.append("rect")
    .attr("class", "view")
    .attr("x", 0.5)
    .attr("y", 0.5)
    .attr("width", width - 1)
    .attr("height", height - 1);

var points = svg.selectAll('circle')
  .data(data)
  .enter();
  
  points
  .append("circle")
  .classed('node', true)
  .attr('r', 5)
  .attr('cx', function (d) {return x(d.x);})
  .attr('cy', function (d) {return y(d.y);})
  .on('click', function(d) {onTokenClick(d);})
  .append('svg:title')
  .text(function (d) {return d.label;});
  
  points
  .append("text")
  .classed('label', true)
  .attr('x', function (d) {return x(d.x);})
  .attr('y', function (d) {return y(d.y);})
  .on('click', function(d) {onTokenClick(d);})
  .text(function (d) {return d.label;})
  .append('svg:title')
  .text(function (d) {return d.label;});
  
d3.select("#reset")
    .on("click", resetted);

d3.select("#clear")
    .on("click", clearSelection);

d3.select("#query_input")
	.on("search", queryToken);

svg.call(zoom);

function zoomed() {
  view.attr("transform", d3.event.transform);
  
  svg.selectAll('.node')
  .data(data)
  .attr('cx', function(d) {return d3.event.transform.rescaleX(x)(d.x);})
  .attr('cy', function(d) {return d3.event.transform.rescaleY(y)(d.y);});
  
  svg.selectAll('.label')
  .data(data)
  .attr('x', function(d) {return d3.event.transform.rescaleX(x)(d.x);})
  .attr('y', function(d) {return d3.event.transform.rescaleY(y)(d.y);});
}

function resetted() {
  clearSelection();
  svg.transition()
    .duration(750)
    .call(zoom.transform, d3.zoomIdentity);
}

function clearQuerySelection() {
  svg.selectAll('.queried')
  	.attr('r', 5)
  	.style('fill', '#BBB')
  	.classed('queried', false);
}

function clearSelection() {
  clearQuerySelection();
  clearSimilarities();
  svg.selectAll('.node').style('fill', '#BBB').classed('selected', false);
  svg.selectAll('.label').style('fill', '#000').classed('selected', false);
  d3.selectAll('#clusters span').remove();
  d3.select('#query_input').node().value = '';
}

function clearSimilarities() {
  d3.select('#similarities h3').remove();
  d3.selectAll('#similarities svg *').remove();
}

function onTokenClick(token) {
  highlight(token);
  showSimilarities(token);
  currentColor = (currentColor + 1) % 10;
}

function highlight(token) {
  var node_selection = svg.selectAll('.node')
  .data(data)
  .filter(function(d) {return d.cluster == token.cluster;});
  
  node_selection.style('fill', colorScale(currentColor)).classed('selected', true);
  
  svg.selectAll('.label')
  .data(data)
  .filter(function(d) {return d.cluster == token.cluster;})
  .style('fill', colorScale(currentColor))
  .classed('selected', true);
  
  d3.select("#clusters")
    .append('span')
    .text(token.label + ' (#' + token.cluster + ', n = ' + node_selection.size() + ')').style('color', colorScale(currentColor))
    .append('br');
}

function showSimilarities(token) {	
	var heading = d3.select('#similarities')
	  .selectAll('h3')
	  .data([token]);
	
	heading  
	  .enter()
	  .insert('h3', ':first-child')
	  .classed('sim-heading', true)
	  .merge(heading)
	  .text(token.label + ' (#' + token.rank + ': ' + token.count +')')
	  .style('color', colorScale(currentColor));
	  
	var sim_svg = d3.select("#similarities > svg");
	var width = sim_svg.node().getBoundingClientRect().width;
	var barHeight = 10;

	sim_svg.attr('height', (barHeight + 2) * token.similarities.length);
	
	var sim_bars = sim_svg 
	  .selectAll('rect')
	  .data(token.similarities, function(d) {return d.other_token;});

	sim_bars.exit().remove();
	sim_bars.enter()
	  .append('rect')
	  .attr('width', function(d) {return d.similarity * 0.5 * width;})
	  .attr('height', barHeight)
	  .attr('x', 0.5 * width)
	  .attr('y', function(d, i) {return (barHeight + 2) * i;})
	  .style('fill', colorScale(currentColor));

	var sim_labels = sim_svg 
	  .selectAll('.sim-label')
	  .data(token.similarities, function(d) {return d.other_token;});
	 
	sim_labels.exit().remove();
	sim_labels.enter()
	  .append('text')
	  .classed('sim-label', true)
	  .attr('x', 0.5 * width - 3)
	  .attr('y', function(d, i) {return (barHeight + 2) * i + 0.5 * barHeight + 1;})
	  .text(function (d) {return d.other_token;})
	  .style('fill', colorScale(currentColor));
}

function queryToken() {
	clearQuerySelection();
	var token = d3.select('#query_input').node().value;
	svg.selectAll('.node')
      .filter(function(d) {return d.label.includes(token);})
      .classed('queried', true)
      .transition()
      .duration(500)
      .attr('r', 20)
      .style('fill', 'blue')
      .transition()
      .duration(750)
      .attr('r', 10)
      .style('fill', 'red');     
}
}
