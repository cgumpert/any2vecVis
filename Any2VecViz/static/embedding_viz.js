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
var svg = d3.select("svg").attr('width', width).attr('height', height);

var zoom = d3.zoom()
    .scaleExtent([1, 50])
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
  .on('click', function(d) {highlight(d.cluster);});
  
  points
  .append("text")
  .classed('label', true)
  .attr('x', function (d) {return x(d.x);})
  .attr('y', function (d) {return y(d.y);})
  .attr('cursor', 'pointer')
  .on('click', function(d) {highlight(d.cluster);})
  .text(function (d) {return d.label;})
  .append('svg:title')
  .text(function (d) {return d.label;});
  
d3.select("#reset")
    .on("click", resetted);

d3.select("#clear")
    .on("click", clearSelection);

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

function clearSelection() {
  svg.selectAll('.node').style('fill', '#BBB').classed('selected', false);
  svg.selectAll('.label').style('fill', '#000').classed('selected', false);
}

function highlight(cluster) {
  svg.selectAll('.node')
  .data(data)
  .filter(function(d) {return d.cluster == cluster;})
  .style('fill', colorScale(currentColor))
  .classed('selected', true);
  
  svg.selectAll('.label')
  .data(data)
  .filter(function(d) {return d.cluster == cluster;})
  .style('fill', colorScale(currentColor))
  .classed('selected', true);
  
  currentColor = (currentColor + 1) % 10;
}
}
