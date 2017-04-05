'use strict';

var SERVER_URL = "https://"+myVar+"/api/v1/"
var BillingAPI_Connector = angular.module('BillingAPI_Connector', [], function($interpolateProvider){
   $interpolateProvider.startSymbol('{-');
   $interpolateProvider.endSymbol('-}');
});

BillingAPI_Connector.factory('myProjects', function($http, $q){
   return{
      getProjects: function(){
         return $http.get(SERVER_URL+'projects')
      }
   }
});

BillingAPI_Connector.factory('myInvoices', function($http, $q){
   return{
      data: function(){
         return $http.get(SERVER_URL+'invoices'); },
      getInvoices: function(project_name) {
         return $http.get(SERVER_URL+'invoices', {params: {project: project_name}});
      }
   }
});


BillingAPI_Connector.controller('billing_controller', function($scope, $http, $compile, $q, myProjects, myInvoices) {
   $scope.projects = [];
   $scope.currentProject = "";
   $scope.invoices = [];
   $scope.activeInvoice = null;
   $scope.viewingDetails = false;
   $scope.welcoming = true;
   var pieArrAnalysis =[];
   var pieArrStack = [];
   $scope.total = "";
   
   myProjects.getProjects().then(
      function (result) {
          $scope.projects = result.data.map(function(project){
              return {project_name: project, selected: false};
          });
      }
   );

   $scope.hasCheck = function (facet, item) {
      if (facet + item in checked_boxes) {
          return true;
      }
      else {
          return false;
      }
   };

   var retrieveInvoice = function(projectname) {
      myInvoices.getInvoices(projectname).then(function(result) {
          $scope.costData = result;
          $scope.invoices = result.data.map(function(invoice) {
              invoice.selected = false;
              return invoice;
          });
         drawProjectChart();
         drawStackedChart();
      });
   };


   $scope.selectInvoice = function (idx) {
      $scope.activeInvoice = idx;
   };

   $scope.selectProject = function (projectName) {
      $scope.currentProject = projectName;
      $scope.projects = $scope.projects.map(function(project) {
          return {project_name: project.project_name, selected: project.project_name === projectName};
      });
      $scope.invoices = [];
      retrieveInvoice(projectName);
      
   };

   $scope.quantizeString = function (moneystring, radix) {
      var retstr = '';
      var foundDecimal = false;
      var afterRadix = 0;
      for(var i = 0; (i < moneystring.length) && (afterRadix <= radix); i++) {
          if(moneystring[i] == '.') {
              foundDecimal = true;
          }
          if(foundDecimal) {
              afterRadix += 1;
          }
          retstr = retstr + moneystring[i];
      }
      return retstr;
   };

   $scope.isActiveProject = function (project) {
      return $scope.currentProject === project;
   };

   $scope.viewDetails = function (invoice_index) {
      $scope.viewingDetails = true;
      $scope.activeInvoice = $scope.invoices[invoice_index];
      $scope.getTotal();
   }
  
   $scope.unviewDetails = function () {
      $scope.viewingDetails = false;
      $scope.activeInvoice = null;
      retrieveInvoice($scope.currentProject);
//       drawProjectChart();
//       drawStackedChart();
   }
  
   $scope.welcome = function(){
      if ($scope.currentProject === ""){
         $scope.welcoming = true;
      }
      else{
         $scope.welcoming = false;
      }
   }
   
   $scope.printPage = function(){
      window.print();
   }
   
   $scope.getTotal = function(){
      $scope.total = "";
      var item = 0;
      for(var i = 0; i < $scope.activeInvoice.by_analysis.itemized_compute_costs.length; i++){
         item = parseFloat($scope.activeInvoice.by_analysis.itemized_compute_costs[i].cost) + item;
      }
      $scope.total = $scope.quantizeString(item.toString(),2);
   }

   //pie charts
   // turns pie data into array format
   $scope.piedata = function(){
      var loopPromises = [];
      var myItem = $scope.currentProject;
         var costtemp = $scope.invoices;
         
         //pie
         var ccost = 0;
         var scost = 0;
         pieArrAnalysis =[];
         var pieTemp = [];
         var pieTemp2 = [];
         
         //bar
         pieArrStack = [];
         var pieTempStack = [];
         pieTempStack.push("Date");
         pieTempStack.push("Compute Cost");
         pieTempStack.push("Storage Cost");
         pieArrStack.push(pieTempStack);
         
         for (var i=0; i<costtemp.length; i++){
            //pie
            ccost = parseFloat(costtemp[i].compute_cost) + ccost;
            scost = parseFloat(costtemp[i].storage_cost) + scost;
            
            //bar
            pieTempStack = [];
            pieTempStack.push(costtemp[i].month_of);
            var stackccost = parseFloat(costtemp[i].compute_cost);
            var stackscost = parseFloat(costtemp[i].storage_cost);
            pieTempStack.push(stackccost);
            pieTempStack.push(stackscost);
            pieArrStack.push(pieTempStack);
         }
         console.log(pieArrStack);
         pieTemp = [];
         pieTemp.push("Compute Cost");
         pieTemp.push(ccost);
         pieTemp2.push(pieTemp);
         pieTemp = [];
         pieTemp.push("Storage Cost");
         pieTemp.push(scost);
         pieTemp2.push(pieTemp);
         for (var i=0; i<pieTemp2.length; i++){
            pieArrAnalysis.push(pieTemp2[i]);
         }
         return pieArrAnalysis;	
   }
   
   //pie chart maker
   var chart;
   google.charts.load('current', {'packages':['corechart']});
   google.charts.setOnLoadCallback(drawProjectChart);
   function drawProjectChart() {
      $scope.piedata();
      var data = new google.visualization.DataTable();
      data.addColumn('string', 'Type');
      data.addColumn('number', 'Number');
      console.log(pieArrAnalysis);
      data.addRows(pieArrAnalysis);

      var options = {
         title: 'Overall Storage and Compute Cost',
         width: 200,
         height: 200,
         legend: 'none',
         fontName: 'Helvetica Neue',
         slices: {
            0: { color: '#1A535C' },
            1: { color: '#4CC9C0' },
            2: { color: '#FF6B6B' },
            3: { color: '#FFA560' },
            4: { color: '#113871' },
            5: { color: '#5C83D0' },
            6: { color: '#FFE66D' }
         }
      };

      chart = new google.visualization.PieChart(document.getElementById('piechartProject'));

      chart.draw(data, options);
   }  
   
   //Stacked bar chart
   function drawStackedChart(){
      console.log(pieArrStack)
      var data = google.visualization.arrayToDataTable(pieArrStack);
      var options = {
         width: 400,
         height: 200,
         legend: { position: 'top', maxLines: 3 },
         bar: { groupWidth: '75%' },
         isStacked: true,
         series: {
            0: { color: '#1A535C' },
            1: { color: '#4CC9C0' },
            2: { color: '#FF6B6B' },
            3: { color: '#FFA560' },
            4: { color: '#113871' },
            5: { color: '#5C83D0' },
            6: { color: '#FFE66D' }
         }
      };
      chart = new google.visualization.ColumnChart(document.getElementById('stackedchart'));

      chart.draw(data, options);
   }







});
