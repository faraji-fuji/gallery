"use strict";
window.addEventListener("load", function () {
  
  document.getElementById("sign-out").onclick = function () {
    document.cookie = "token=";
    window.location.href = "/";
    console.log("logged out on button click")
    // ask firebase to sign out the user
    firebase.auth().signOut().then(function() {
      document.cookie = "token=";
    }).catch(function(error) {
      console.error("Error signing out:", error);
    });
  };

  var uiConfig = {
    signInSuccessUrl: "/",
    signInOptions: [firebase.auth.EmailAuthProvider.PROVIDER_ID],
  };

  firebase.auth().onAuthStateChanged(
    function (user) {
      if (user) {
        document.getElementById("sign-out").hidden = false;
        document.getElementById("main-content").hidden = false;
        // document.getElementById("main-content").hidden = false;
        console.log(`Signed in as ${user.displayName} (${user.email})`);
        
        user.getIdToken().then(function (token) {
          document.cookie = "token=" + token;

          console.log(`COOKIE VALUE AUTH: ${document.cookie}`)
        });

        


      } else {
        var ui = new firebaseui.auth.AuthUI(firebase.auth());
        ui.start("#firebase-auth-container", uiConfig);
        document.getElementById("sign-out").hidden = true;
        document.getElementById("main-content").hidden = true;
        document.cookie = "token=";
        console.log(`COOKIE VALUE UNAUTH: ${document.cookie}`)
      }
    },
    function (error) {
      console.log(error);
      alert("Unable to log in: " + error);
    }
  );

});
