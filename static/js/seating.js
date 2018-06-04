(function () {
    'use strict';

// TODO: get all this from the backend
    const loggedInUserId = 0;

// NOTE: The emails are used for gravatars, however given we probably don't
// want to send the email address of everyone to anyone who looks at the
// seating plan this could trivially be refactored to send the gravatar hash
// instead (email.trim().toLower().md5()), this would also allow us to not
// include md5.js
    const users = [
        {id: 0, nickname: 'zed0', email: 'ben@falconers.me.uk'},
        {id: 1, nickname: 'rhiba', email: 'rhiannon.michelmore@gmail.com'},
        {id: 2, nickname: 'Tankski', email: 'dr.tankski@gmail.com'},
        // {
        //     id: 3,
        //     nickname: 'Lorem ipsum dolor sit amet',
        //     email: 'a@b.com'
        // },
        // {id: 4, nickname: 'Some name with <marquee>html content</marquee>', email: 'b@b.com'},
    ];

    const seatingRevisions = [
        {id: 0, seatHasUser: {1: 0, 2: 1, 8: 2}},
        {id: 1, seatHasUser: {2: 0, 3: 1, 4: 2}},
        {id: 2, seatHasUser: {7: 0, 8: 1, 9: 2, 11: 3}},
        {id: 3, seatHasUser: {10: 0, 11: 1}},
        {id: 4, seatHasUser: {20: 0, 21: 1}},
    ];

    let currentSeatHasUser;
    let dragging = false;
    let draggingUser;
    let unassignedUsers;

    let svgDom;
    let unassignedDom;
    let containerDom;
    let popupDom;
    let revisionLogDom;
    let commitButtonDom;

    function removeUserFromOldLocation(userId) {
        const oldSeatId = Object.keys(currentSeatHasUser).find(key => currentSeatHasUser[key] === userId);
        if (oldSeatId !== undefined) {
            currentSeatHasUser[oldSeatId] = undefined;
            const oldSeat = svgDom.querySelectorAll('[data-seat-id="' + oldSeatId + '"]')[0];
            updateSeatStyle(oldSeat);
        }

        if (unassignedUsers.find(user => user.id === userId)) {
            unassignedUsers = unassignedUsers.filter(user => user.id !== userId);
            const element = unassignedDom.querySelectorAll('[data-user-id="' + userId + '"]')[0];
            element.parentElement.removeChild(element);
        }
    }

    function giveUnassignedToUser(userId) {
        removeUserFromOldLocation(userId);

        unassignedUsers = unassignedUsers
            .concat(users.find(user => user.id === userId))
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
        removeUserFromOldLocation(userId);

        currentSeatHasUser[seat.dataset.seatId] = userId;
        updateSeatStyle(seat);
    }

    function dragStart(user, event) {
        const popupUsernameDom = popupDom.getElementsByClassName('seating-username')[0];
        popupUsernameDom.innerHTML = '';
        popupUsernameDom.appendChild(document.createTextNode(user.nickname));

        popupDom.getElementsByClassName('seating-avatar')[0].src = gravatarUrl(user.email);
        popupDom.dataset.userId = user.id;
        popupDom.style.display = 'flex';

        dragSetPosition(event);

        dragging = true;
        draggingUser = user;

        event.stopPropagation();
        event.preventDefault ? event.preventDefault() : event.returnValue = false;
    }

    function dragStop(event) {
        if (!dragging)
            return;

        popupDom.style.display = 'none';
        dragging = false;
        draggingUser = undefined;
    }

    function dragStopOnSeat(event) {
        if (!dragging)
            return;

        const seat = this;
        if (currentSeatHasUser[seat.dataset.seatId] === undefined)
            giveSeatToUser(seat, draggingUser.id);

        dragStop(event);
    }

    function dragStopOnUnassigned(event) {
        if (!dragging)
            return;

        giveUnassignedToUser(draggingUser.id);

        dragStop(event);
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
            const seatUser = users.find(user => user.id === seatUserId);
            dragStart(seatUser, event);
        }
    };

    function dragStartOnUnassignedUser(event) {
        const unassignedUserDom = this;
        const userId = parseInt(unassignedUserDom.dataset.userId, 10);

        const user = users.find(user => user.id === userId);
        dragStart(user, event);
    };

    function onClickRevision(event) {
        const revisionDom = this;
        const revisionId = parseInt(revisionDom.dataset.revisionId, 10);
        updateToRevision(revisionId);
    }

    function gravatarUrl(email) {
        const base = 'http://www.gravatar.com/avatar/';
        const hash = md5(email.trim().toLowerCase());
        const tail = '?d=identicon&s=200';
        return base + hash + tail;
    }

    function gravatarIdForUser(user) {
        return 'gravatar-' + user.id;
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
            seat.style.fill = '';
            seat.style.cursor = '';
        }
        else {
            const seatUser = users.find(user => user.id === seatUserId);
            seat.style.fill = 'url(#' + gravatarIdForUser(seatUser) + ')';
            seat.style.cursor = 'move';
        }

        if (seatUserId === loggedInUserId) {
            // Unfortuantely due to this being in a different document we can't share
            // this with the sass variable
            seat.style.stroke = 'rgba(228, 232, 255, 0.7)';
        }
        else {
            seat.style.stroke = '';
        }
    }

    function highlightSeatIfDragging(event) {
        if (!dragging)
            return;

        const seat = this;
        const seatUserId = currentSeatHasUser[seat.dataset.seatId];
        if (seatUserId === undefined)
            seat.style.fill = '#5a6771';
        else
            seat.style.cursor = 'no-drop';
    }

    function unhighlightSeat(event) {
        const seat = this;
        const seatUserId = currentSeatHasUser[seat.dataset.seatId];
        if (seatUserId === undefined)
            seat.style.fill = '';
        else
            seat.style.cursor = 'move';
    }

    function updateToRevision(revisionId) {
        const newRevision = seatingRevisions.find(revision => revision.id === revisionId);
        // It is important to break the reference here so we don't corrupt the original revision
        currentSeatHasUser = Object.assign({}, newRevision.seatHasUser);

        unassignedUsers = users
            .filter(user => Object.values(currentSeatHasUser).indexOf(user.id) === -1)
            .sort(sortByNickname);

        refreshUnassigned();
        refreshSeats();
    }

    function refreshUnassigned() {
        unassignedDom.innerHTML = '';
        unassignedUsers.forEach(user => {
            const avatar = document.createElement('img');
            avatar.src = gravatarUrl(user.email);
            const nickname = document.createElement('span');
            nickname.appendChild(document.createTextNode(user.nickname));
            const unassignedUserDiv = document.createElement('div');
            unassignedUserDiv.appendChild(avatar);
            unassignedUserDiv.appendChild(nickname);
            unassignedUserDiv.classList.add('unassigned-user');
            unassignedUserDiv.classList.add('level');
            unassignedUserDiv.dataset.userId = user.id;
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
        // TODO: Send this to the backend and get the new seatingRevisions array from there
        const maxId = Math.max.apply(Math, seatingRevisions.map(rev => rev.id));

        const newRevision = {
            id: maxId + 1,
            // Make sure to break the reference so the committed revision doesn't continue to be updated
            seatHasUser: Object.assign({}, currentSeatHasUser),
        };
        seatingRevisions.push(newRevision);
        addRevisionButton(newRevision);
    }

    function addRevisionButton(revision) {
        const node = document.createElement('a');
        node.dataset.revisionId = revision.id;
        node.appendChild(document.createTextNode('Revision ' + revision.id));
        node.classList.add('revision');
        node.addEventListener('click', onClickRevision);

        revisionLogDom.appendChild(node);
        revisionLogDom.appendChild(document.createElement('br'));
    }

    document.addEventListener('DOMContentLoaded', function () {
        svgDom = document.getElementById('seating-chart').getElementsByTagName('svg')[0];
        unassignedDom = document.getElementById('seating-unassigned');
        containerDom = document.getElementById('seating-chart-container');
        popupDom = document.getElementById('seating-chart-popup');
        revisionLogDom = document.getElementById('seating-revision-log');
        commitButtonDom = document.getElementById('seating-commit-button');

        commitButtonDom.addEventListener('click', commitRevision);
        containerDom.addEventListener('mousemove', dragMove);
        containerDom.addEventListener('touchmove', dragMove);
        containerDom.addEventListener('mouseup', dragStop);
        containerDom.addEventListener('touchend', handleTouchEnd);
        unassignedDom.parentElement.addEventListener('mouseup', dragStopOnUnassigned);
        unassignedDom.parentElement.addEventListener('touchend', handleTouchEnd);

        seatingRevisions.forEach(revision => {
            addRevisionButton(revision);
        });

        users.forEach(user => {
            createSvgPattern(gravatarIdForUser(user), gravatarUrl(user.email));
        });

        const seats = svgDom.getElementsByClassName('seat');
        // For some reason HTMLCollection doesn't have .forEach or .map :(
        for (let i = 0; i < seats.length; ++i) {
            const seat = seats[i];
            seat.addEventListener('mousedown', dragStartOnSeat);
            seat.addEventListener('touchstart', dragStartOnSeat);
            seat.addEventListener('mouseup', dragStopOnSeat);
            seat.addEventListener('touchend', handleTouchEnd);
            seat.addEventListener('mouseenter', highlightSeatIfDragging);
            seat.addEventListener('mouseout', unhighlightSeat);
        }

        updateToRevision(seatingRevisions[seatingRevisions.length - 1].id);
    });

})();
