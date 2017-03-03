'use strict';

var SERVER_URL = "https://dev.ucsc-cgl.org/api/v1/"
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
BillingAPI_Connector.controller('billing_controller', function($scope, $http, $compile, myProjects, myInvoices) {
	   $scope.projects = [];
	      $scope.currentProject = "";
	         $scope.invoices = [];
		    $scope.activeInvoice = null;
		       $scope.viewingDetails = false;
		          $scope.welcoming = true;
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
							           $scope.invoices = result.data.map(function(invoice) {
									                 invoice.selected = false;
											               return invoice;
												                 });
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
								         }
						    
						     $scope.unviewDetails = function () {
							           $scope.viewingDetails = false;
								         $scope.activeInvoice = null;
									    }
						       
						        $scope.welcome = function(){
								      if ($scope.currentProject === ""){
									               $scope.welcoming = true;
										             }
								            else{
										             $scope.welcoming = false;
											           }
									       }

});
