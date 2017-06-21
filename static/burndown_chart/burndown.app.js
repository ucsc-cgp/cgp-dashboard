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
   $scope.colors = ['#45b7cd', '#ff6384', '#ff8e72'];
   $scope.onClick = function (points, evt) {
      console.log(points, evt);
   };
   $scope.datasetOverride = [{ yAxisID: 'y-axis-1' }];

   $scope.options = {
      title: {
         display: true,
         text: 'RNA-Seq'
      },
      scales: {
         yAxes: [
            {
               id: 'y-axis-1',
               type: 'linear',
               display: true,
               position: 'left',
               scaleLabel: {
                  display: true,
                  labelString: 'Number of Jobs'
               },
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
         ],
         xAxes: [
            {
               scaleLabel: {
                  display: true,
                  labelString: 'Timestamp'
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
