(function () {
    'use strict';

    const users = [];

    let seatingRevisions = [];
    let unassignedUsers;
    let revisionNumber = null;

    let currentSeatHasUser;
    let dragging = false;
    let draggingUser;

    let svgDom;
    let unassignedDom;
    let containerDom;
    let popupDom;
    let revisionLogDom;
    let commitButtonDom;
    let notificationDom;
    let notificationTextDom;
    let notificationCloseDom;

    function removeUserFromOldLocation(userId) {
        const oldSeatId = Object.keys(currentSeatHasUser).find(key => currentSeatHasUser[key] === userId);
        if (oldSeatId !== undefined) {
            currentSeatHasUser[oldSeatId] = undefined;
            const oldSeat = svgDom.querySelectorAll('[data-seat-id="' + oldSeatId + '"]')[0];
            updateSeatStyle(oldSeat);
        }

        if (unassignedUsers.find(user => user.user_id === userId)) {
            unassignedUsers = unassignedUsers.filter(user => user.user_id !== userId);
            const element = unassignedDom.querySelectorAll('[data-user-id="' + userId + '"]')[0];
            element.parentElement.removeChild(element);
        }
    }

    function giveUnassignedToUser(userId) {
        enableSave();
        removeUserFromOldLocation(userId);

        unassignedUsers = unassignedUsers
            .concat(users.find(user => user.user_id === userId))
            .sort(sortByNickname);

        refreshUnassigned();
    }

    function sortByNickname(a, b) {
        if (a.nickname < b.nickname)
            return -1;
        if (a.nickname > b.nickname)
            return 1;
        return 0;
    }

    function giveSeatToUser(seat, userId) {
        enableSave();
        removeUserFromOldLocation(userId);

        currentSeatHasUser[seat.dataset.seatId] = userId;
        updateSeatStyle(seat);
    }

    function dragStart(user, event) {
        containerDom.classList.add('seating-chart-dragging');
        const popupUsernameDom = popupDom.getElementsByClassName('seating-username')[0];
        popupUsernameDom.innerHTML = '';
        popupUsernameDom.appendChild(document.createTextNode(user.nickname));

        popupDom.getElementsByClassName('seating-avatar')[0].src = user.avatar;
        popupDom.dataset.userId = user.user_id;
        popupDom.classList.remove('is-hidden');

        dragSetPosition(event);

        dragging = true;
        draggingUser = user;

        event.stopPropagation();
        event.preventDefault ? event.preventDefault() : event.returnValue = false;
    }

    function dragStop(event) {
        if (!dragging)
            return;

        containerDom.classList.remove('seating-chart-dragging');
        popupDom.classList.add('is-hidden');
        dragging = false;
        draggingUser = undefined;
    }

    function dragStopOnSeat(event) {
        if (!dragging)
            return;

        const seat = this;
        if (currentSeatHasUser[seat.dataset.seatId] === undefined)
            giveSeatToUser(seat, draggingUser.user_id);

        dragStop(event);
        if (revisionNumber === null)
            commitRevision();
    }

    function dragStopOnUnassigned(event) {
        if (!dragging)
            return;

        giveUnassignedToUser(draggingUser.user_id);

        dragStop(event);
        if (revisionNumber === null)
            commitRevision();
    }

    function handleTouchEnd(event) {
        const changedTouch = event.changedTouches[0];
        const elem = document.elementFromPoint(changedTouch.clientX, changedTouch.clientY);

        if (elem === unassignedDom.parentElement || unassignedDom.parentElement.contains(elem))
            dragStopOnUnassigned(event);
        else if (elem.getAttribute('class') === 'seat')
            dragStopOnSeat.bind(elem, event)();
        else
            dragStop(event);
    }

    function dragSetPosition(event) {
        const offsetLeft = -containerDom.getBoundingClientRect().left;
        const offsetTop = -containerDom.getBoundingClientRect().top;

        const clientX = event.touches ? event.touches[0].clientX : event.clientX;
        const clientY = event.touches ? event.touches[0].clientY : event.clientY;

        let divOffsetLeft = 0;
        let divOffsetTop = window.scrollY;

        if (clientX + popupDom.getBoundingClientRect().width > (window.innerWidth || document.documentElement.clientWidth) - 25) {
            divOffsetLeft += -popupDom.getBoundingClientRect().width;
        }

        if (clientY + popupDom.getBoundingClientRect().height > (window.innerHeight || document.documentElement.clientHeight) - 5) {
            divOffsetTop += -popupDom.getBoundingClientRect().height;
        }

        popupDom.style.left = divOffsetLeft + clientX + 2 + 'px';
        popupDom.style.top = divOffsetTop + clientY + 2 + 'px';
    }

    function dragMove(event) {
        if (!dragging)
            return;

        dragSetPosition(event);
        event.preventDefault ? event.preventDefault() : event.returnValue = false;
    }

    function dragStartOnSeat(event) {
        const seat = this;
        const seatUserId = currentSeatHasUser[seat.dataset.seatId];

        if (seatUserId !== undefined) {
            const seatUser = users.find(user => user.user_id === seatUserId);
            dragStart(seatUser, event);
        }
    };

    function dragStartOnUnassignedUser(event) {
        const unassignedUserDom = this;
        const userId = parseInt(unassignedUserDom.dataset.userId, 10);

        const user = users.find(user => user.user_id === userId);
        dragStart(user, event);
    };

    function onClickRevision(event) {
        const revisionDom = this;
        const revisionId = parseInt(revisionDom.dataset.revisionId, 10);
        updateToRevision(revisionId);
    }

    function avatarIdForUser(user) {
        return 'avatar-' + user.user_id;
    }

    function createSvgPattern(id, url) {
        const pattern = document.createElementNS('http://www.w3.org/2000/svg', 'pattern');
        pattern.setAttribute('id', id);
        pattern.setAttribute('patternContentUnits', 'objectBoundingBox');
        pattern.setAttribute('preserveAspectRatio', 'xMidYMid slice');
        pattern.setAttribute('width', '1');
        pattern.setAttribute('height', '1');
        pattern.setAttribute('viewBox', '0 0 1 1');

        const image = document.createElementNS('http://www.w3.org/2000/svg', 'image');
        image.setAttribute('preserveAspectRatio', 'xMidYMid slice');
        image.setAttributeNS('http://www.w3.org/1999/xlink', 'xlink:href', url);
        image.setAttribute('width', '1');
        image.setAttribute('height', '1');
        pattern.appendChild(image);

        svgDom.querySelector('defs').appendChild(pattern);
    }

    function updateSeatStyle(seat) {
        const seatUserId = currentSeatHasUser[seat.dataset.seatId];

        if (seatUserId === undefined) {
            seat.classList.remove('user-seat');
            seat.style.fill = '';
        }
        else {
            const seatUser = users.find(user => user.user_id === seatUserId);
            seat.classList.add('user-seat');
            seat.style.fill = 'url(#' + avatarIdForUser(seatUser) + ')';
        }

        if (seatUserId === loggedInUserId)
            seat.classList.add('logged-in-user-seat');
        else
            seat.classList.remove('logged-in-user-seat');
    }

    function refreshUnassigned() {
        unassignedDom.innerHTML = '';
        unassignedUsers.forEach(user => {
            const avatar = document.createElement('img');
            avatar.src = user.avatar;
            const nickname = document.createElement('span');
            nickname.appendChild(document.createTextNode(user.nickname));
            const unassignedUserDiv = document.createElement('div');
            unassignedUserDiv.appendChild(avatar);
            unassignedUserDiv.appendChild(nickname);
            unassignedUserDiv.classList.add('unassigned-user');
            unassignedUserDiv.classList.add('level');
            unassignedUserDiv.dataset.userId = user.user_id;
            unassignedUserDiv.addEventListener('mousedown', dragStartOnUnassignedUser);
            unassignedUserDiv.addEventListener('touchstart', dragStartOnUnassignedUser);

            unassignedDom.appendChild(unassignedUserDiv);
        });
    }

    function refreshSeats() {
        const seats = svgDom.getElementsByClassName('seat');
        // For some reason HTMLCollection doesn't have .forEach or .map :(
        for (let i = 0; i < seats.length; ++i) {
            const seat = seats[i];
            updateSeatStyle(seat);
        }
    }

    function commitRevision(event) {
        disableSave();

        const seatsToBackendFormat = input => Object.keys(input)
            .filter(key => input[key] !== undefined)
            .map(key => ({seat_id: parseInt(key, 10), user_id: input[key]}));
        const layout = {
            seats: seatsToBackendFormat(currentSeatHasUser),
        };
        const eventSubmitUrl = '/seating/api/submit/' + eventId;
        ajax(eventSubmitUrl, 'POST', 'json=' + JSON.stringify(layout), (status, response) => {
            if (status !== 200) {
                enableSave();
                addError('There was an error saving your changes.');
            }
            else {
                finishSave('Saved');
                if (response.length && isExec) {
                    addRevision(JSON.parse(response).revision);
                    revisionNumber = null;
                }
            }
        });
    }

    function addRevision(revision) {
        if (seatingRevisions.find(a => a.number === revision.number) === undefined) {
            seatingRevisions.unshift(revision);

            const listElement = document.createElement('li');
            const anchor = document.createElement('a');
            anchor.dataset.revisionId = revision.number;
            anchor.appendChild(document.createTextNode(revision.name));
            anchor.classList.add('revision');
            anchor.addEventListener('click', onClickRevision);

            listElement.appendChild(anchor);
            revisionLogDom.insertBefore(listElement, revisionLogDom.childNodes[0]);
        }
    }

    function disableSave() {
        commitButtonDom.disabled = true;
    }

    function finishSave() {
        commitButtonDom.disabled = true;
        commitButtonDom.innerHTML = '<i class="fas fa-check"></i>Saved';
    }

    function enableSave() {
        commitButtonDom.innerHTML = '<i class="fas fa-save"></i>Save';
        commitButtonDom.disabled = false;
    }


    function ajax(url, method, body, callback) {
        const csrf = Cookies.get('csrftoken');
        const http = new XMLHttpRequest();

        http.open(method, url, true);
        http.setRequestHeader('X-CSRFToken', csrf);
        if (method !== 'GET')
            http.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');

        http.onload = function () {
            callback(http.status, http.response);
        };
        http.onerror = function () {
            callback(http.status, http.response);
        };
        try {
            http.send(body);
        }
        catch (e) {
            callback(http.status, http.response);
        }
    }

    function addError(errorText) {
        notificationTextDom.append(document.createTextNode(errorText));
        notificationDom.classList.remove('is-hidden');
    }

    function clearError() {
        notificationDom.classList.add('is-hidden');
        notificationTextDom.innerHTML = '';
    }

    function updateToRevision(revision = null) {
        let eventSeatingUrl = '/seating/api/seats/' + eventId;
        if (revision !== null)
            eventSeatingUrl = eventSeatingUrl + '?revision=' + revision;

        ajax(eventSeatingUrl, 'GET', null, (status, response) => {
            if (status !== 200) {
                addError('The seating configuration could not be retrieved.');
            }
            else {
                const currentRevision = JSON.parse(response);

                currentSeatHasUser = {};
                unassignedUsers = [];

                currentRevision.seated.forEach(userSeat => {
                    currentSeatHasUser[userSeat.seat_id] = userSeat.user_id;
                    users.push(userSeat);
                });

                currentRevision.unseated.forEach(userSeat => {
                    users.push(userSeat);
                    unassignedUsers.push(userSeat);
                });

                users.forEach(user => {
                    createSvgPattern(avatarIdForUser(user), user.avatar);
                });

                refreshUnassigned();
                refreshSeats();

                if (revision !== null) {
                    revisionNumber = revision;
                    enableSave();
                }
            }
        });
    }

    function updateRevisionList() {
        if (!isExec)
            return;

        const eventRevisionsUrl = '/seating/api/revisions/' + eventId;
        ajax(eventRevisionsUrl, 'GET', null, (status, response) => {
            if (status !== 200) {
                addError('The current revision log could not be retrieved.');
            }
            else {
                JSON.parse(response).revisions
                    .sort((a, b) => a.number - b.number)
                    .map(addRevision);
            }
        });
    }


    document.addEventListener('DOMContentLoaded', function () {
        svgDom = document.getElementById('seating-chart').getElementsByTagName('svg')[0];
        unassignedDom = document.getElementById('seating-unassigned');
        containerDom = document.getElementById('seating-chart-container');
        popupDom = document.getElementById('seating-chart-popup');
        revisionLogDom = document.getElementById('seating-revision-log');
        commitButtonDom = document.getElementById('seating-commit-button');
        notificationDom = document.getElementById('seating-error-notification');
        notificationTextDom = notificationDom.querySelectorAll('span')[0];
        notificationCloseDom = notificationDom.getElementsByClassName('delete')[0];

        commitButtonDom.addEventListener('click', commitRevision);
        containerDom.addEventListener('mousemove', dragMove);
        containerDom.addEventListener('touchmove', dragMove);
        // Triggering this on the popup too makes dragging a lot smoother
        popupDom.addEventListener('mousemove', dragMove);
        containerDom.addEventListener('mouseup', dragStop);
        containerDom.addEventListener('touchend', handleTouchEnd);
        unassignedDom.parentElement.addEventListener('mouseup', dragStopOnUnassigned);
        unassignedDom.parentElement.addEventListener('touchend', handleTouchEnd);

        const seats = svgDom.getElementsByClassName('seat');
        // For some reason HTMLCollection doesn't have .forEach or .map :(
        for (let i = 0; i < seats.length; ++i) {
            const seat = seats[i];
            seat.addEventListener('mousedown', dragStartOnSeat);
            seat.addEventListener('touchstart', dragStartOnSeat);
            seat.addEventListener('mouseup', dragStopOnSeat);
            seat.addEventListener('touchend', handleTouchEnd);
        }

        notificationCloseDom.addEventListener('click', clearError);

        updateToRevision(null);
        updateRevisionList();
        setInterval(() => {
            if (!dragging && revisionNumber === null)
                updateToRevision(null);

            updateRevisionList();
        }, 5000);
    });

})();
