"use strict";
window.addEventListener("load", function () {
  document.getElementById("sign-out").onclick = function () {
    // ask firebase to sign out the user
    firebase.auth().signOut();
  };

  var uiConfig = {
    signInSuccessUrl: "/gallery/index/",
    signInOptions: [firebase.auth.EmailAuthProvider.PROVIDER_ID],
  };

  firebase.auth().onAuthStateChanged(
    function (user) {
      if (user) {
        document.getElementById("sign-out").hidden = false;
        document.getElementById("main-content").hidden = false;
        // document.getElementById("main-content").hidden = false;
        console.log("Signed in as ${user.displayName} (${user.email})");
        user.getIdToken().then(function (token) {
          document.cookie = "token=" + token;
        });
      } else {
        var ui = new firebaseui.auth.AuthUI(firebase.auth());
        ui.start("#firebase-auth-container", uiConfig);
        document.getElementById("sign-out").hidden = true;
        document.getElementById("main-content").hidden = true;
        document.getElementById("main-content").hidden = true;

        document.cookie = "token=";
      }
    },
    function (error) {
      console.log(error);
      alert("Unable to log in: " + error);
    }
  );
});
