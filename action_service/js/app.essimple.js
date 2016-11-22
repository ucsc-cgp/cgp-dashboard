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
         return $http.get('http://ucsc-cgl.org:8080/action_service/js/action_index.jsonl');
      }
   }
});

//Factory with parameters
MyAPI_Connector.factory('myParams', function($http){
   return{
      data: function(){
         return $http.get('http://ucsc-cgl.org:8080/action_service/js/action_index.jsonl');
      }
   }
});



//Controller for the page
MyAPI_Connector.controller('API_Controller', function($scope, $http, $compile, myService, myParams){
   //Variables to be used to populate the page
   $scope.hits = [];
   $scope.results = [];
   
   //Assign the termFacets and hits to the scope variables
   var assign_Hits_Facets = function(data){
   	console.log(data);
      $scope.results = data.data;
      $scope.hits = data.data.data;
   }
   //Get a regular default call to the API
   var get_myService = function(){
      myService.data().then(function(data){
         assign_Hits_Facets(data);
         //get_myPaging(data);
         //Call the pie charts initially //////TEST
         return;
      });
   }
   
   //Call the regular service to populate the webpage initially
   get_myService();
   

});

