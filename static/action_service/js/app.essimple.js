'use strict';

//Set MyAPI_Connector
var MyAPI_Connector = angular.module('MyAPI_Connector', [], function($interpolateProvider){
   $interpolateProvider.startSymbol('{-');
   $interpolateProvider.endSymbol('-}');
});

MyAPI_Connector.factory('myService', function($http){
   return{
      data: function(){
         return $http.get('https://'+myVar+'/api/v1/action/service');
      }
   }
});

//Controller for the page
MyAPI_Connector.controller('API_Controller', function($scope, $http, $compile, myService){
   $scope.results = []; 

   //Get a regular default call to the API
   var get_myService = function(){
      myService.data().then(function(data){
         $scope.results = data.data;
         //get_myPaging(data);
         //Call the pie charts initially //////TEST
         return;
      });
   }
   
   get_myService();
});

