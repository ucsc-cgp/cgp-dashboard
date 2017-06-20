'use strict';

var timeStamps = captured_dates;
var allJobs = total_jobs;
var completedJobs = finished_jobs;

var BurndownAPI_Connector = angular.module('BurndownAPI_Connector', ["chart.js"], function($interpolateProvider){
   $interpolateProvider.startSymbol('{-');
   $interpolateProvider.endSymbol('-}');
});

BurndownAPI_Connector.controller('burndown_controller', function($scope) {
   $scope.labels = timeStamps;
   $scope.series = ['All Jobs', 'Finished Jobs'];
   $scope.data = [allJobs, completedJobs];
   $scope.onClick = function (points, evt) {
      console.log(points, evt);
   };
   $scope.datasetOverride = [{ yAxisID: 'y-axis-1' }];

   $scope.options = {
      scales: {
         yAxes: [
            {
               id: 'y-axis-1',
               type: 'linear',
               display: true,
               position: 'left',
               ticks: {
                  min: 0,
                  beginAtZero: true,
                  callback: function(value, index, values) {
                     if (value % 1 === 0) {
                        return value;
                     }
                  }
               }
            }
         ]
      },
      elements: {
         line: {
            tension: 0
         }
      } 
   };
});
