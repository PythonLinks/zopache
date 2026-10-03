 var tootButton = document.getElementById("form-action-toot");
 var tootViewButton = document.getElementById("form-action-tootView");
var textArea =  document.getElementById('textBox');

 function displayCharacters(){
  
    var tootString = document.getElementById("form-field-toot").value;
     var tootLength = countCharacters(tootString)
    
    var remainingCharacters = 500 - tootLength;

    var style;
    if (remainingCharacters <= 0){
        style = 'color:red';
        textArea.style.backgroundColor= "red";
        tootButton.disabled = true;
        tootViewButton.disabled = true;

    }
    else{
        style = '';
        textArea.style.backgroundColor = "white";
        tootButton.disabled = false;
        tootViewButton.disabled = false;
      
    }
    var result = `<span style = "${style}">  ${remainingCharacters}</span>`;
    document.getElementById('length').innerHTML = result;
 }
textArea.oninput = displayCharacters;
 displayCharacters();


  function possibleLogin(){
    if (! canToot){ 
	var url = "https://"+
	           window.location.hostname +
	          "/person/oauth";	    
      window.open(url);
 }
 }
