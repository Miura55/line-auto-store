"use strict";

if (typeof define === "function" && define.amd) {
  define(["jquery"]);
} else if (typeof exports === "object") {
  if (typeof $ === "undefined") {
    module.exports = require("jquery");
  } else {
    module.exports = $;
  }
}

var modalTemplate = {
  dialog:
    '<div id="boot4alert" class="modal fade">' +
    '<div class="modal-dialog">' +
    '<div class="modal-content">' +
    '<div class="modal-body"></div>' +
    "</div>" +
    "</div>" +
    "</div>",
  header:
    '<div class="modal-header">' + '<h5 class="modal-title"></h5>' + "</div>",
  footer: '<div class="modal-footer"></div>',
  closeButton:
    '<button class="close" style="margin-top: -15px;"  data-dismiss="modal">' +
    "<span>&times;</span>" +
    "</button>",
  button:
    '<button class="btn btn-primary boot4ok" data-dismiss="modal" type="button"></button>',
  buttonConfirm:
    '<button class="btn btn-secondary boot4cancel" data-dismiss="modal" type="button">Cancel</button>' +
    '<button class="btn btn-primary boot4ok" data-dismiss="modal" type="button">OK</button>'
};

var dialog = $(modalTemplate.dialog);
var body = dialog.find(".modal-body");
var callbacks = {
  onEscape: ""
};

function Initial(msg, btnMsg) {
  var tmsg = "";

  if (
    (msg.callback != undefined || msg.confirm) &&
    !$.isFunction(msg.callback)
  ) {
    throw new Error("alert requires callback property to be a function");
  }

  if (msg.msg != undefined) {
    tmsg = msg.msg;
  } else if (msg.title != undefined) {
    tmsg = msg.msg;
  } else {
    tmsg = msg + modalTemplate.closeButton;
  }

  if (msg.title != undefined && dialog.find(".modal-header").length == 0) {
    body.before(modalTemplate.header);
    dialog.find(".modal-header").html(msg.title + modalTemplate.closeButton);
  }

  if (msg.style != undefined) {
    dialog.find(".modal-header").css(msg.style);
  }

  if (dialog.find(".btn-primary").length == 0) {
    body.after(modalTemplate.footer);
    if (msg.confirmBox != undefined) {
      dialog.find(".modal-footer").html(modalTemplate.buttonConfirm);
    } else {
      dialog.find(".modal-footer").html(modalTemplate.button);
      dialog.find(".btn").html(btnMsg);
    }
  }
  dialog.find(".modal-body").html(tmsg);
  if (msg.size != undefined) {
    switch (msg.size) {
      case "sm":
        dialog.find(".modal-dialog").addClass("modal-sm");
        break;
      case "lg":
        dialog.find(".modal-dialog").addClass("modal-lg");
        break;
      case "xl":
        dialog.find(".modal-dialog").addClass("modal-xl");
        break;
      default:
        break;
    }
  }
}

var boot4 = {
  alert: function(msg, btnMsg, options) {
    Initial(msg, btnMsg);
    $("body").append(dialog);
    if (msg.callback != undefined) {
      $("#boot4alert").modal(options);
      return (callbacks.onEscape = msg.callback);
    } else {
      return $("#boot4alert").modal(options);
    }
  },
  confirm: function(msg, options) {
    msg.confirmBox = true;
    Initial(msg);
    $("body").append(dialog);
    $("#boot4alert").modal(options);
    return (callbacks.onEscape = msg.callback);
  }
};

function processCallback(e, dialog, callback, result) {
  e.stopPropagation();
  e.preventDefault();
  var preserveDialog =
    $.isFunction(callback) && callback.call(dialog, result, e) === false;
  if (!preserveDialog) {
    dialog.modal("hide");
  }
}
dialog.on("click", ".boot4ok", function(e) {
  processCallback(e, dialog, callbacks.onEscape, true);
});
dialog.on("click", ".boot4cancel", function(e) {
  processCallback(e, dialog, callbacks.onEscape, false);
});
