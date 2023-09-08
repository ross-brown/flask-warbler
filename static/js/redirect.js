"use strict";

let seconds = 4;
const url = '/';

function redirect() {
  if (seconds <= 0) {
    window.location = url;
  } else {
    seconds--;
    document.querySelector(".redirect-countdown").innerHTML =
      `Redirecting to Home after ${seconds} seconds.`;
      setTimeout(redirect(), 1000)
  }
}
