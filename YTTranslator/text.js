function userStatus() {
}
let isLoggedIn = false;
let userExists = true;
if (userExists) {
    let isLoggedIn = true; // Different variable, scoped to this block
    console.log(isLoggedIn); // true
}