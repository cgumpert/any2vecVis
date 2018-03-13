var data = [
  {
    id: 0,
    x: 1.3,
    y: -2.3,
    label: 'hello',
    cluster: 3
  },
  {
    id: 1,
    x: -1.3,
    y: 2.3,
    label: 'welt',
    cluster: 1
  },
  {
    id: 2,
    x: -1.5,
    y: 2.7,
    label: 'bla',
    cluster: 1
  },
  {
    id: 3,
    x: -0.3,
    y: 1.3,
    label: 'foo',
    cluster: 1
  },
  {
    id: 4,
    x: 1.5,
    y: -3,
    label: 'bar',
    cluster: 0
  }
];

// set svg to full screen
var width = window.innerWidth - 2;
var height = window.innerHeight - 2;
var svg = d3.select("svg").attr('width', width).attr('height', height);

var zoom = d3.zoom()
    .scaleExtent([1, 40])
    .translateExtent([[-100, -100], [width + 90, height + 100]])
    .on("zoom", zoomed);

var x = d3.scaleLinear()
    .domain([-10, 10])
    .range([-1, width + 1]);

var y = d3.scaleLinear()
    .domain([-10, 10])
    .range([-1, height + 1]);

var xAxis = d3.axisBottom(x)
    .ticks((width + 2) / (height + 2) * 10)
    .tickSize(5)
    .tickPadding(8);

var yAxis = d3.axisRight(y)
    .ticks(10)
    .tickSize(5)
    .tickPadding(8);

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
  .attr('cx', function (d) {console.log(d); return x(d.x);})
  .attr('cy', function (d) {return y(d.y);});
  
  points
  .append("text")
  .classed('label', true)
  .attr('x', function (d) {console.log(d); return x(d.x);})
  .attr('y', function (d) {return y(d.y);})
  .attr('cursor', 'pointer')
  .on('click', function(d) {clearSelection(); highlight(d.cluster);})
  .text(function (d) {return d.label;})
  .append('svg:title')
  .text(function (d) {return d.label;});
  
d3.select("button")
    .on("click", resetted);

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
  svg.selectAll('.node').classed('selected', false);
  svg.selectAll('.label').classed('selected', false);
}

function highlight(cluster) {
  svg.selectAll('.node')
  .data(data)
  .filter(function(d) {return d.cluster == cluster;})
  .classed('selected', true);
  
  svg.selectAll('.label')
  .data(data)
  .filter(function(d) {return d.cluster == cluster;})
  .classed('selected', true);
}
