'use strict';

//Deleted all the old code, this talks to the API service

var MyAPI_Connector = angular.module('MyAPI_Connector', []);

//Parameter variable
var config = {
   params:{
      filters: null

   }
}
var my_filters = {'file':{}};
var configManifest = {
   params:{
      filters: null
   }
}

//Set up the factory, whatever that means
MyAPI_Connector.factory('myService', function($http){
   return{
      data: function(){
         return $http.get('http://ec2-35-164-176-8.us-west-2.compute.amazonaws.com:5000/files/');
      }
   }
});

//Factory with parameters
MyAPI_Connector.factory('myParams', function($http){
   return{
      data: function(){
         return $http.get('http://ec2-35-164-176-8.us-west-2.compute.amazonaws.com:5000/files/', config);
      }
   }
});

//Factory for the manifest endpoint. 
MyAPI_Connector.factory('myManifest', function($http){
   return{
      data: function(){
         return $http.get('http://ec2-35-164-176-8.us-west-2.compute.amazonaws.com:5000/files/export', config); //Have to fix the filter system variable. It needs the specific verbose
      }
   }
});

//Controller for the page
MyAPI_Connector.controller('API_Controller', function($scope, $http, $compile, myService, myParams, myManifest){
   //Variables to be used to populate the page
   $scope.hits = [];
   $scope.results = [];
   $scope.offset = 0;
   $scope.poutof = 0;
   $scope.of = "of";
   $scope.back = "Back";
   $scope.next = "Next";
   $scope.pageSize = 0;
   $scope.nextPages = true;
   $scope.backPages = true;
   //for the manifest file
   $scope.numHits = 0;
   $scope.manData;
   $scope.bodyArr = [];
   var bodyStr;
   //for the pie charts
   var pieArrAnalysis =[];
   var pieArrWorkflow =[];
   var pieArrFile =[];
   //Keeps track of boxes checked
   var checked_boxes = {};
   //Map for the filters whenever they are used.
   //var my_filters = {'file':{}};
   
   var field_dict = {};


   //Assigns the pagination data
   var get_myPaging = function(data){
      $scope.offset = data.data.pagination.page;
      $scope.poutof = data.data.pagination.pages;
      $scope.pageSize = data.data.pagination.size;
      verify();
      //refresh(0);
   }
   //Holds the Manifest data
   var get_myManData = function(data){
      //$scope.manData = data.data.hits;
      console.log("at get_myManData");
      console.dir($scope.manData);
      //bodydown();

   }
   
   //Assign the termFacets and hits to the scope variables
   var assign_Hits_Facets = function(data){
      $scope.results = data.data.termFacets;
      $scope.hits = data.data.hits;
      $scope.numHits = data.data.pagination.total;
   }
   //Get a regular default call to the API
   var get_myService = function(){
      myService.data().then(function(data){
         assign_Hits_Facets(data);
         get_myPaging(data);
         //Call the pie charts initially //////TEST
         drawAnalysisChart();
         drawWorkflowChart();
         drawFileChart();
         return;
      });
   }
   //Make a call to the API when parameters are included
   var get_myParams = function(){
      myParams.data().then(function(data){
         assign_Hits_Facets(data);
         get_myPaging(data);
         //updates pie charts
         drawAnalysisChart();
         drawWorkflowChart();
         drawFileChart();
         return;
      });
   }
   //Make a call to the API for Manifest file
   var get_myManifest = function(){
      myManifest.data().then(function(data){
         var file = new File([data.data], {type: "text/plain;charset=utf-8"})
         saveAs(file, 'manifest.tsv')
         return data;
         console.log("at get_myManifest");
         //return;
      });
   }
   
   //adds facet, for clicking multiple facets
   var adding_Facet = function(facet, item){
      if (!(facet in field_dict)){
         field_dict[facet] = [item];
      }
      else{
         field_dict[facet].push(item);
      }
   }
   
   var deleting_Facet = function(facet, item){
      if(field_dict[facet].length == 1){
         delete field_dict[facet];
         delete my_filters['file'][facet];
      }
      else{
         var index = field_dict[facet].indexOf(item);
         delete field_dict[facet].splice(index, 1);;
      }
      console.log(field_dict);
   }
   
   //Call the regular service to populate the webpage initially
   get_myService();
   //Function to be called whenever a checkbox is marked; applies the filters. 
   $scope.checking = function(facet, item){
   	console.log(item);
      if(!(facet+item in checked_boxes)){
         //Add the checked box to the array containing all the checked boxes
         adding_Facet(facet, item);
         checked_boxes[facet+item] = 1;
         //Set the parameter
         for (var key in field_dict){
            my_filters['file'][key] = {'is': field_dict[key]}; 
         }
         console.log(my_filters);
         //Delete the from field in the config structure
         delete config['params']['from'];
         //Apply the parameters and make the call to the server
         config['params']['filters'] = my_filters;
         get_myParams();
      }
      else{
         //Delete the unchecked filters and call again the web service
         delete checked_boxes[facet+item];
         deleting_Facet(facet, item);
         var size = 0;
         for (var key in field_dict){
            my_filters['file'][key] = {'is': field_dict[key]}; 
            size++;
         } 
         console.log(my_filters);
         if (size > 0){
            config['params']['filters'] = my_filters;
         }
         else{
            config['params']['filters'] = null;
         }
         //This is where you call the web service again. 
         get_myParams();

      }
      console.log(checked_boxes);
   }
   //Conditions to allow the checkbox to be either checked or unchecked
   $scope.hasCheck = function(facet, item){
      if(facet+item in checked_boxes){
         return true;
      }
      else{
         return false;
      }
   }
   //Verify whether the Next or Back button should be hidden
   var verify = function(){
      console.log($scope.offset);
      console.log($scope.poutof);
      if($scope.offset == 1){
         $scope.backPages = false;
         $scope.nextPages = true;
      }
      else if($scope.offset == $scope.poutof){
         $scope.nextPages = false;
         $scope.backPages = true;
      }
      else{
         $scope.nextPages = true;
         $scope.backPages = true;
      }
   }
   //Whenever Next or Back is clicked:
   $scope.refresh = function(pcount){
      var goToPage = $scope.offset+pcount;
      //console.log($scope.offset);
      //Set the parameters to call next batch of items
      verify();
      config['params']['from'] = (goToPage*$scope.pageSize) - $scope.pageSize +1;
      get_myParams();
      verify();
   }
   
   //download as manifest helper function
   //TO BE DELETED
   var bodydown = function(){
      $scope.bodyArr = [];
      for (var i=0; i<$scope.numHits; i++){
         var projectDown = $scope.manData[i]['project'];
         var donorDown = $scope.manData[i]['donor'];
         var specimen_typeDown = $scope.manData[i]['specimen_type'];
         var analysis_typeDown = $scope.manData[i]['analysis_type'];
         var workflowDown = $scope.manData[i]['workflow'];
         var file_typeDown = $scope.manData[i]['file_type'];
         var titleDown = $scope.manData[i]['title'];
         var download_idDown = $scope.manData[i]['download_id'];
         $scope.bodyArr.push(projectDown+"\t"+donorDown+"\t"+specimen_typeDown+"\t"+analysis_typeDown+"\t"+workflowDown+"\t"+file_typeDown+"\t"+titleDown+"\t"+download_idDown);
      }
      bodyStr = $scope.bodyArr[0];
      for (var i=1;i<$scope.numHits;i++){
         bodyStr = bodyStr.concat("\n");
         bodyStr = bodyStr.concat($scope.bodyArr[i]);
      }
   }
   
   //download Manifest file
   $scope.downloadfile = function(){
      //configManifest = config;
      var number_size = config['params']['size'];
      config['params']['size'] = $scope.numHits;
      
      console.log(config);
      console.log(configManifest);
      //verify();
      console.log("calling get_myManifest");
      get_myManifest();
      console.log("after calling get_myManifest");
      console.log("calling makingManifest()");
      //makingManifest();
      console.log("after calling makingManifest()");
      config['params']['size'] = number_size;
      verify();
   }
   //TO BE DELETED
   var makingManifest = function(){
      var titledown = "Project\tDonor\tSpecimen\tType\tAnalysis Type\tWorkflow\tFile Type\tFile\tDownload ID"
      
      var file = new File([titledown+"\n"+bodyStr], "results.tsv", {type: "text/plain;charset=utf-8"});
      saveAs(file);
      config['params']['size'] = null;
      console.log("end of calling makingManifest()");
   }
   
   // turns pie data into array format
   $scope.piedata = function(){
   	console.log($scope.results);
      pieArrAnalysis =[];
      var pieTemp = [];
      var pieTemp2 = [];
      for (var i=0; i<$scope.results.analysisType.terms.length; i++){
         pieTemp = [];
         pieTemp.push($scope.results.analysisType.terms[i].term);
         pieTemp.push($scope.results.analysisType.terms[i].count);
         pieTemp2.push(pieTemp);
      }
      for (var i=0; i<$scope.results.analysisType.terms.length; i++){
         pieArrAnalysis.push(pieTemp2[i]);
      }
      pieArrWorkflow =[];
      pieTemp2 = [];
      for (var i=0; i<$scope.results.workFlow.terms.length; i++){
         pieTemp = [];
         pieTemp.push($scope.results.workFlow.terms[i].term);
         pieTemp.push($scope.results.workFlow.terms[i].count);
         pieTemp2.push(pieTemp);
      }
      for (var i=0; i<$scope.results.workFlow.terms.length; i++){
         pieArrWorkflow.push(pieTemp2[i]);
      }
      pieArrFile =[];
      pieTemp2 = [];
      for (var i=0; i<$scope.results.fileFormat.terms.length; i++){
         pieTemp = [];
         pieTemp.push($scope.results.fileFormat.terms[i].term);
         pieTemp.push($scope.results.fileFormat.terms[i].count);
         pieTemp2.push(pieTemp);
      }
      for (var i=0; i<$scope.results.fileFormat.terms.length; i++){
         pieArrFile.push(pieTemp2[i]);
      }
   }
   
   //pie chart maker
   var chart;
   google.charts.load('current', {'packages':['corechart']});
   google.charts.setOnLoadCallback(drawAnalysisChart);
   function drawAnalysisChart() {
      $scope.piedata($scope.numHits);
      var data = new google.visualization.DataTable();
      data.addColumn('string', 'Type');
      data.addColumn('number', 'Number');
      data.addRows(pieArrAnalysis);

      var options = {
         title: 'Analysis Type',
         width: 200,
         height: 200,
         legend: 'none',
         fontName: 'Muli'
      };

      chart = new google.visualization.PieChart(document.getElementById('piechartAnalysis'));

      chart.draw(data, options);
   }      
   google.charts.setOnLoadCallback(drawWorkflowChart);
   function drawWorkflowChart() {
      $scope.piedata($scope.numHits);
      var data = new google.visualization.DataTable();
      data.addColumn('string', 'Type');
      data.addColumn('number', 'Number');
      data.addRows(pieArrWorkflow);
      
      var options = {
         title: 'Workflow Type',
         width: 200,
         height: 200,
         legend: 'none',
         fontName: 'Muli'
      };

      chart = new google.visualization.PieChart(document.getElementById('piechartWorkflow'));

      chart.draw(data, options);
   }    
   google.charts.setOnLoadCallback(drawFileChart);
   function drawFileChart() {
      $scope.piedata($scope.numHits);
      var data = new google.visualization.DataTable();
      data.addColumn('string', 'Type');
      data.addColumn('number', 'Number');
      data.addRows(pieArrFile);
      
      var options = {
         title: 'File Type',
         width: 200,
         height: 200,
         legend: 'none',
         fontName: 'Muli'
      };

      chart = new google.visualization.PieChart(document.getElementById('piechartFile'));

      chart.draw(data, options);
   }  

});

