// some generic functions for selecting/deselecting/deleting a number of table entries

function toggleall(f,icheck,allcheck) {
    chk = document.forms[f.name].elements[icheck];
    if (document.forms[f.name].elements[allcheck].checked == true) {
        // if only one test, no array
        if (typeof chk.length == 'undefined') {
            chk.checked = true;
        } else {
            for (i = 0; i < chk.length; i++) {
                chk[i].checked = true;
            }
        }
    } else {
        if (typeof chk.length == 'undefined') {
            chk.checked = false;
        } else {
            for (i = 0; i < chk.length; i++) {
                chk[i].checked = false;
            }
        }
    }
}

function buildlist(f,icheck,ilist) {
    chk = document.forms[f.name].elements[icheck];
    llist = '';
    if (typeof chk.length == 'undefined') {
        llist = chk.value;
    } else {
        for (i = 0; i < chk.length; i++) {
            if (chk[i].checked == true) {
               llist = llist + chk[i].value + ",";
            }
        }
    }
    document.forms[f.name].elements[ilist].value = llist;
}

