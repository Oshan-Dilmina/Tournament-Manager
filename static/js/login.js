
const firebaseConfig = {
    apiKey: "AIzaSyDhtpT0fgtKtIyUvMNI45dKn4qchg8Wtb4",
    authDomain: "tournament-mgr-caf10.firebaseapp.com",
    projectId: "tournament-mgr-caf10",
};

if (!firebase.apps.length) {
    firebase.initializeApp(firebaseConfig);
}

const ui = new firebaseui.auth.AuthUI(firebase.auth());

const uiConfig = {
    signInOptions: [
        firebase.auth.EmailAuthProvider.PROVIDER_ID,
        firebase.auth.GoogleAuthProvider.PROVIDER_ID
    ],
    signInFlow: 'popup',
    callbacks: {
        uiShown: function() {
            document.getElementById('loader').style.display = 'none';
        },
        signInSuccessWithAuthResult: function(authResult) {
            document.getElementById('loader').style.display = 'block';
            document.getElementById('firebaseui-auth-container').style.display = 'none';

            // Send Verification Email if user just signed in/up
            if (authResult.user) {
                authResult.user.sendEmailVerification().then(() => {
                    console.log("Verification email sent.");
                });
            }

            authResult.user.getIdToken().then(function(idToken) {
                return fetch('/api/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ idToken: idToken })
                });
            }).then(response => {
                if (response.ok) {
                    window.location.href = '/'; // Hardcoded path
                } else {
                    alert("Server-side authentication failed.");
                    window.location.reload();
                }
            });
            return false;
        }
    }
};

firebase.auth().onAuthStateChanged(function(user) {
    ui.start('#firebaseui-auth-container', uiConfig);
});