from __future__ import absolute_import
# =========================== imports =========================================

from builtins import range
from builtins import object
import random
import sys
from abc import abstractmethod

import netaddr
import time
import SimEngine
from . import MoteDefines as d
from . import sixp

# =========================== defines =========================================

# =========================== helpers =========================================

# =========================== body ============================================

class SchedulingFunction(object):
    def __new__(cls, mote):
        settings    = SimEngine.SimSettings.SimSettings()
        class_name  = u'SchedulingFunction{0}'.format(settings.sf_class)
        return getattr(sys.modules[__name__], class_name)(mote)

class SchedulingFunctionBase(object):

    SLOTFRAME_HANDLE = 0

    def __init__(self, mote):

        # store params
        self.mote            = mote

        # singletons (quicker access, instead of recreating every time)
        self.settings        = SimEngine.SimSettings.SimSettings()
        self.engine          = SimEngine.SimEngine.SimEngine()
        self.log             = SimEngine.SimLog.SimLog().log

    # ======================= public ==========================================

    # === admin

    @abstractmethod
    def start(self):
        """
        tells SF when should start working
        """
        raise NotImplementedError() # abstractmethod

    @abstractmethod
    def stop(self):
        '''
        tells SF when should stop working
        '''
        raise NotImplementedError() # abstractmethod

    # === indications from other layers

    @abstractmethod
    def indication_neighbor_added(self, neighbor_mac_addr):
        pass

    @abstractmethod
    def indication_tx_cell_elapsed(self, cell, sent_packet):
        """[from TSCH] just passed a dedicated TX cell. used=False means we didn't use it.

        """
        raise NotImplementedError() # abstractmethod

    @abstractmethod
    def indication_rx_cell_elapsed(self, cell, received_packet):
        raise NotImplementedError() # abstractmethod

    @abstractmethod
    def indication_parent_change(self, old_parent, new_parent):
        """
        [from RPL] decided to change parents.
        """
        raise NotImplementedError() # abstractmethod

    @abstractmethod
    def detect_schedule_inconsistency(self, peerMac):
        raise NotImplementedError() # abstractmethod

    @abstractmethod
    def recv_request(self, packet):
        raise NotImplementedError() # abstractmethod

    @abstractmethod
    def clear_to_send_EBs_DATA(self):
        raise NotImplementedError() # abstractmethod


class SchedulingFunctionSFNone(SchedulingFunctionBase):

    def __init__(self, mote):
        super(SchedulingFunctionSFNone, self).__init__(mote)

    def start(self):
        pass # do nothing

    def stop(self):
        pass # do nothing

    def indication_neighbor_added(self, neighbor_mac_addr):
        pass # do nothing

    def indication_tx_cell_elapsed(self, cell, sent_packet):
        pass # do nothing

    def indication_rx_cell_elapsed(self, cell, received_packet):
        pass # do nothing

    def indication_parent_change(self, old_parent, new_parent):
        pass # do nothing

    def detect_schedule_inconsistency(self, peerMac):
        pass # do nothing

    def recv_request(self, packet):
        pass # do nothing

    def clear_to_send_EBs_DATA(self):
        # always return True
        return True


class SchedulingFunctionMSF(SchedulingFunctionBase):

    SLOTFRAME_HANDLE_AUTONOMOUS_CELLS = 1
    SLOTFRAME_HANDLE_NEGOTIATED_CELLS = 2
    DEFAULT_CELL_LIST_LEN = 5
    MAX_RETRY = 3
    TX_CELL_OPT   = [d.CELLOPTION_TX]
    RX_CELL_OPT   = [d.CELLOPTION_RX]
    NUM_INITIAL_NEGOTIATED_TX_CELLS = 1
    NUM_INITIAL_NEGOTIATED_RX_CELLS = 0
    RTEW=5
    L=[0,0,1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,12,12,13,13,14,14,15,15,16,16,17,17,18,18,19,19,20,20,21,21,22,22,23,23,24,24,25,25,26,26,27,27,28,28]
    por=[1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,12,12,13,13,14,14,15,15,16,16,17,17,18,18,19,19,20,20,21,21,22,22,23,23,24,24,25,25]
   
    taken=[]
    hops=1
    S4=[3,3,4,4,5,5,6,6,7,7,8,8,9,9]
    S5=[4,4,5,5,6,6,7,7,8,8,9,9]
    S6=[3,3,4,4,5,5,6,6,7,7,8,8,9,9]
    S7=[3,3,4,4,5,5,6,6,7,7,8,8,9,9]
    S8=[3,3,4,4,5,5,6,6,7,7,8,8,9,9]
    takenS4=[]
    takenS5=[]
    takenS6=[]
    takenS7=[]
    takenS8=[]
    takenS9=[]
    takenS10=[]
    takenS11=[]
    takenS12=[]
    takenS13=[]
    takenS14=[]
    takenS15=[]
    takenS16=[]
    takenS17=[]
    takenS18=[]
    takenS19=[]
    takenS20=[]
    takenS21=[]
    takenS22=[]
    takenS23=[]
    takenS24=[]
    takenS25=[]
    takenS26=[]
    takenS27=[]
    takenS28=[]
    takenS29=[]
    takenS30=[]

    takenS31=[]
    takenS32=[]
    takenS33=[]



    def __init__(self, mote):
        # initialize parent class
        super(SchedulingFunctionMSF, self).__init__(mote)

        # (additional) local variables
        self.num_tx_cells_elapsed = 0
        self.num_tx_cells_used    = 0
        self.tx_cell_utilization  = 0
        self.num_rx_cells_elapsed = 0
        self.num_rx_cells_used    = 0
        self.rx_cell_utilization  = 0
        self.locked_slots         = set([]) # slots in on-going ADD transactions
        self.retry_count          = {}      # indexed by MAC address

    # ======================= public ==========================================

    # === admin

    def start(self):
        # install slotframes for MSF, which have the same length as
        # Slotframe 0
        slotframe_0 = self.mote.tsch.get_slotframe(0)
        self.mote.tsch.add_slotframe(
            slotframe_handle = self.SLOTFRAME_HANDLE_AUTONOMOUS_CELLS,
            length           = slotframe_0.length
        )
        self.mote.tsch.add_slotframe(
            slotframe_handle = self.SLOTFRAME_HANDLE_NEGOTIATED_CELLS,
            length           = slotframe_0.length
        )

        # install our autonomous RX cell
        self.allocate_autonomous_rx_cell()

        if self.mote.dagRoot:
            # do nothing
            pass
        else:
            self._housekeeping_collision()

    def stop(self):
        # uninstall the slotframes entirely instead of removing the
        # cells there one by one
        self.mote.tsch.delete_slotframe(self.SLOTFRAME_HANDLE_AUTONOMOUS_CELLS)
        self.mote.tsch.delete_slotframe(self.SLOTFRAME_HANDLE_NEGOTIATED_CELLS)

        if self.mote.dagRoot:
            # do nothing
            pass
        else:
            self.engine.removeFutureEvent(
                (self.mote.id, u'_housekeeping_collision')
            )

    # === indications from other layers

    def indication_neighbor_added(self, neighbor_mac_addr):
        pass

    def indication_tx_cell_elapsed(self, cell, sent_packet):
        preferred_parent = self.mote.rpl.getPreferredParent()
        if (
                preferred_parent
                and
                (cell.mac_addr == preferred_parent)
                and
                (cell.options == [d.CELLOPTION_TX])
            ):
            self._update_cell_counters(self.TX_CELL_OPT, bool(sent_packet))
            # adapt number of cells if necessary
            if d.MSF_MAX_NUMCELLS <= self.num_tx_cells_elapsed:
                tx_cell_utilization = (
                    self.num_tx_cells_used /
                    float(self.num_tx_cells_elapsed)
                )
                if tx_cell_utilization != self.tx_cell_utilization:
                    self.log(
                        SimEngine.SimLog.LOG_MSF_TX_CELL_UTILIZATION,
                        {
                            u'_mote_id'    : self.mote.id,
                            u'neighbor'    : preferred_parent,
                            u'value'       : u'{0}% -> {1}%'.format(
                                int(self.tx_cell_utilization * 100),
                                int(tx_cell_utilization * 100)
                            )
                        }
                    )
                    self.tx_cell_utilization = tx_cell_utilization
                self._adapt_to_traffic(preferred_parent, self.TX_CELL_OPT)
                self._reset_cell_counters(self.TX_CELL_OPT)

    def indication_rx_cell_elapsed(self, cell, received_packet):
        preferred_parent = self.mote.rpl.getPreferredParent()
        if not preferred_parent:
            # nothing to do
            return

        if (
                (cell.mac_addr == preferred_parent)
                and
                (cell.options == [d.CELLOPTION_RX])
            ):
            self._handle_rx_cell_elapsed_event(bool(received_packet))
        elif (
                (cell.mac_addr == None)
                and
                (
                    cell.slotframe.slotframe_handle ==
                    self.SLOTFRAME_HANDLE_AUTONOMOUS_CELLS
                )
            ):
            if (
                received_packet is None
                or
                received_packet[u'mac'][u'srcMac'] == preferred_parent
                ):
                if not self.get_negotiated_rx_cells(preferred_parent):
                    self._handle_rx_cell_elapsed_event(bool(received_packet))
                else:
                    # ignore this notification
                    pass
            elif (
                self.get_negotiated_rx_cells(received_packet[u'mac'][u'srcMac'])
                ):
                self._handle_rx_cell_elapsed_event(False)
                assert cell.options == [d.CELLOPTION_RX]
                # we received a packet on our autonomous RX cell, with the
                # source mote of which we have negotiated RX cells. The
                # source mote must have lost the negotaited RX cells, TX
                # on its viewpoint. Remove them now.
                self._clear_cells(received_packet[u'mac'][u'srcMac'])

    def indication_parent_change(self, old_parent, new_parent):
        assert old_parent != new_parent

        # allocate the same number of cells to the new parent as it has for the
        # old parent; note that there could be three types of cells:
        # (TX=1,RX=1,SHARED=1), (TX=1), and (RX=1)
        if old_parent is None:
            num_tx_cells = self.NUM_INITIAL_NEGOTIATED_TX_CELLS
            num_rx_cells = self.NUM_INITIAL_NEGOTIATED_RX_CELLS
        else:
            dedicated_cells = self.mote.tsch.get_cells(
                mac_addr         = old_parent,
                slotframe_handle = self.SLOTFRAME_HANDLE_NEGOTIATED_CELLS
            )
            num_tx_cells = len(
                [cell for cell in dedicated_cells if cell.options == [d.CELLOPTION_TX]]
            )
            if num_tx_cells < self.NUM_INITIAL_NEGOTIATED_TX_CELLS:
                num_tx_cells = self.NUM_INITIAL_NEGOTIATED_TX_CELLS
            num_rx_cells = len(
                [cell for cell in dedicated_cells if cell.options == [d.CELLOPTION_RX]]
            )
            if num_rx_cells < self.NUM_INITIAL_NEGOTIATED_RX_CELLS:
                num_rx_cells = self.NUM_INITIAL_NEGOTIATED_RX_CELLS
        if new_parent:
            # reset the retry counter
            # we may better to make sure there is no outstanding
            # transaction with the same peer
            self.retry_count[new_parent] = 0
            self._request_adding_cells(
                neighbor       = new_parent,
                num_tx_cells   = num_tx_cells,
                num_rx_cells   = num_rx_cells
            )

        # clear all the cells allocated for the old parent
        def _callback(event, packet):
            if event == d.SIXP_CALLBACK_EVENT_FAILURE:
                # optimization which is not mentioned in 6P/MSF spec: remove
                # the outstanding transaction because we're deleting all the
                # cells scheduled to the peer now. The outstanding transaction
                # should have the same transaction key as the packet we were
                # trying to send.
                self.mote.sixp.abort_transaction(
                    initiator_mac_addr=packet[u'mac'][u'srcMac'],
                    responder_mac_addr=packet[u'mac'][u'dstMac']
                )
            self._clear_cells(old_parent)

        if old_parent:
            cells = self.mote.tsch.get_cells(
                mac_addr         = old_parent,
                slotframe_handle = self.SLOTFRAME_HANDLE_NEGOTIATED_CELLS
            )
            if len(cells) >= 1:
                self.mote.sixp.send_request(
                    dstMac   = old_parent,
                    command  = d.SIXP_CMD_CLEAR,
                    callback = _callback
                )
            else:
                # do nothing
                pass

    def detect_schedule_inconsistency(self, peerMac):
        # send a CLEAR request to the peer
        self.mote.sixp.send_request(
            dstMac   = peerMac,
            command  = d.SIXP_CMD_CLEAR,
            callback = lambda event, packet: self._clear_cells(peerMac)
        )

    def recv_request(self, packet):
        if   packet[u'app'][u'code'] == d.SIXP_CMD_ADD:
            self._receive_add_request(packet)
        elif packet[u'app'][u'code'] == d.SIXP_CMD_DELETE:
            self._receive_delete_request(packet)
        elif packet[u'app'][u'code'] == d.SIXP_CMD_CLEAR:
            self._receive_clear_request(packet)
        elif packet[u'app'][u'code'] == d.SIXP_CMD_RELOCATE:
            self._receive_relocate_request(packet)
        else:
            # not implemented or not supported
            # ignore this request
            pass

    def clear_to_send_EBs_DATA(self):
        # True if we have a TX cell to the current parent
        slotframe = self.mote.tsch.get_slotframe(self.SLOTFRAME_HANDLE_NEGOTIATED_CELLS)
        parent_addr = self.mote.rpl.getPreferredParent()
        if (
                (slotframe is None)
                or
                (parent_addr is None)
            ):
            tx_cells = []
        else:
            tx_cells = [
                cell for cell in slotframe.get_cells_by_mac_addr(parent_addr)
                if cell.options == [d.CELLOPTION_TX]
            ]

        if self.mote.dagRoot:
            ret_val = True
        else:
            ret_val = bool(tx_cells)

        return ret_val

    def get_tx_cells(self, mac_addr):
        slotframe = self.mote.tsch.get_slotframe(
            self.SLOTFRAME_HANDLE_NEGOTIATED_CELLS
        )
        if slotframe:
            cells = slotframe.get_cells_by_mac_addr(mac_addr)
            # print(cells)
            negotiated_tx_cells = [cell for cell in cells
                                   if cell.options == [d.CELLOPTION_TX]]
            autonomous_tx_cell = self.get_autonomous_tx_cell(mac_addr)
            if negotiated_tx_cells:
                assert not autonomous_tx_cell
                ret = negotiated_tx_cells
            elif autonomous_tx_cell:
                ret = [autonomous_tx_cell]
            else:
                ret = []
        else:
            ret = []
        return ret

    def get_negotiated_rx_cells(self, mac_addr):
        slotframe = self.mote.tsch.get_slotframe(
            self.SLOTFRAME_HANDLE_NEGOTIATED_CELLS
        )
        if slotframe:
            cells = slotframe.get_cells_by_mac_addr(mac_addr)
            ret = [
                cell for cell in cells
                if cell.options == [d.CELLOPTION_RX]
            ]
        else:
            ret = []
        return ret

    def get_autonomous_rx_cell(self):
        slotframe = self.mote.tsch.get_slotframe(
            self.SLOTFRAME_HANDLE_AUTONOMOUS_CELLS
        )
        if slotframe:
            cells = slotframe.get_cells_by_mac_addr(None)
            if cells:
                assert len(cells) == 1
                assert cells[0].options == [d.CELLOPTION_RX]
                ret = cells[0]
            else:
                ret = None
        else:
            ret = None
        return ret

    def allocate_autonomous_rx_cell(self):
        mac_addr = self.mote.get_mac_addr()
        slot_offset, channel_offset = self._compute_autonomous_cell(mac_addr)
        self.mote.tsch.addCell(
            slotOffset       = slot_offset,
            channelOffset    = channel_offset,
            neighbor         = None,
            cellOptions      = [
                d.CELLOPTION_RX
            ],
            slotframe_handle = self.SLOTFRAME_HANDLE_AUTONOMOUS_CELLS
        )

    def get_autonomous_tx_cell(self, mac_addr):
        slotframe = self.mote.tsch.get_slotframe(
            self.SLOTFRAME_HANDLE_AUTONOMOUS_CELLS
        )
        if slotframe:
            cells = slotframe.get_cells_by_mac_addr(mac_addr)
            autonomous_cells = [
                cell for cell in cells
                if (
                        (d.CELLOPTION_TX in cell.options)
                        and
                        (d.CELLOPTION_SHARED in cell.options)
                )
            ]
            if autonomous_cells:
                assert len(autonomous_cells) == 1
                ret = autonomous_cells[0]
            else:
                ret = None
        else:
            ret = None
        return ret

    def allocate_autonomous_tx_cell(self, mac_addr):
        slot_offset, channel_offset = self._compute_autonomous_cell(mac_addr)
        self.mote.tsch.addCell(
            slotOffset       = slot_offset,
            channelOffset    = channel_offset,
            neighbor         = mac_addr,
            cellOptions      = [
                d.CELLOPTION_TX,
                d.CELLOPTION_SHARED
            ],
            slotframe_handle = self.SLOTFRAME_HANDLE_AUTONOMOUS_CELLS
        )

    def deallocate_autonomous_tx_cell(self, mac_addr):
        slot_offset, channel_offset = self._compute_autonomous_cell(mac_addr)
        self.mote.tsch.deleteCell(
            slotOffset       = slot_offset,
            channelOffset    = channel_offset,
            neighbor         = mac_addr,
            cellOptions      = [
                d.CELLOPTION_TX,
                d.CELLOPTION_SHARED
            ],
            slotframe_handle = self.SLOTFRAME_HANDLE_AUTONOMOUS_CELLS
        )

    # ======================= private ==========================================

    def _reset_cell_counters(self, cell_opt):
        if cell_opt == self.TX_CELL_OPT:
            self.num_tx_cells_elapsed = 0
            self.num_tx_cells_used = 0
        else:
            assert cell_opt == self.RX_CELL_OPT
            self.num_rx_cells_elapsed = 0
            self.num_rx_cells_used = 0

    def _handle_rx_cell_elapsed_event(self, used_by_parent):
        preferred_parent = self.mote.rpl.getPreferredParent()
        self._update_cell_counters(self.RX_CELL_OPT, used_by_parent)
        # adapt number of cells if necessary
        rx_cell_utilization = (
            self.num_rx_cells_used /
            float(self.num_rx_cells_elapsed)
        )
        if d.MSF_MAX_NUMCELLS <= self.num_rx_cells_elapsed:
            if rx_cell_utilization != self.rx_cell_utilization:
                self.log(
                    SimEngine.SimLog.LOG_MSF_RX_CELL_UTILIZATION,
                    {
                        u'_mote_id'    : self.mote.id,
                        u'neighbor'    : preferred_parent,
                        u'value'       : u'{0}% -> {1}%'.format(
                            int(self.rx_cell_utilization * 100),
                            int(rx_cell_utilization * 100)
                        )
                    }
                )
                self.rx_cell_utilization = rx_cell_utilization
            self._adapt_to_traffic(preferred_parent, self.RX_CELL_OPT)
            self._reset_cell_counters(self.RX_CELL_OPT)

    def _update_cell_counters(self, cell_opt, used):
        if cell_opt == self.TX_CELL_OPT:
            self.num_tx_cells_elapsed += 1
            if used:
                self.num_tx_cells_used += 1
        else:
            assert cell_opt == self.RX_CELL_OPT
            self.num_rx_cells_elapsed += 1
            if used:
                self.num_rx_cells_used += 1

    def _adapt_to_traffic(self, neighbor, cell_opt):
        # reset retry counter
        assert neighbor in self.retry_count
        if self.retry_count[neighbor] != -1:
            # we're in the middle of a 6P transaction; try later
            return

        if cell_opt == self.TX_CELL_OPT:
            if d.MSF_LIM_NUMCELLSUSED_HIGH < self.tx_cell_utilization:
                # add one TX cell
                self.retry_count[neighbor] = 0
                self._request_adding_cells(
                    neighbor     = neighbor,
                    num_tx_cells = 1
                )

            elif self.tx_cell_utilization < d.MSF_LIM_NUMCELLSUSED_LOW:
                tx_cells = [cell for cell in self.mote.tsch.get_cells(
                        neighbor,
                        self.SLOTFRAME_HANDLE_NEGOTIATED_CELLS
                    ) if cell.options == [d.CELLOPTION_TX]]
                # delete one *TX* cell but we need to keep one dedicated
                # cell to our parent at least
                if len(tx_cells) > 1:
                    self.retry_count[neighbor] = 0
                    self._request_deleting_cells(
                        neighbor     = neighbor,
                        num_cells    = 1,
                        cell_options = self.TX_CELL_OPT
                    )
        else:
            assert cell_opt == self.RX_CELL_OPT
            if d.MSF_LIM_NUMCELLSUSED_HIGH < self.rx_cell_utilization:
                self.retry_count[neighbor] = 0
                self._request_adding_cells(
                    neighbor     = neighbor,
                    num_tx_cells = 0,
                    num_rx_cells = 1,
                )

            elif self.rx_cell_utilization < d.MSF_LIM_NUMCELLSUSED_LOW:
                rx_cells = [cell for cell in self.mote.tsch.get_cells(
                        neighbor,
                        self.SLOTFRAME_HANDLE_NEGOTIATED_CELLS
                    ) if cell.options == [d.CELLOPTION_RX]]
                # delete one *TX* cell but we need to keep one dedicated
                # cell to our parent at least
                if len(rx_cells) > self.NUM_INITIAL_NEGOTIATED_RX_CELLS:
                    self.retry_count[neighbor] = 0
                    self._request_deleting_cells(
                        neighbor     = neighbor,
                        num_cells    = 1,
                        cell_options = self.RX_CELL_OPT
                    )


    def _housekeeping_collision(self):
        """
        Identify cells where schedule collisions occur.
        draft-chang-6tisch-msf-01:
            The key for detecting a schedule collision is that, if a node has
            several cells to the same preferred parent, all cells should exhibit
            the same PDR.  A cell which exhibits a PDR significantly lower than
            the others indicates than there are collisions on that cell.
        :return:
        """

        if self.mote.tsch.get_slotframe(self.SLOTFRAME_HANDLE_NEGOTIATED_CELLS) is None:
            return

        # for quick access; get preferred parent
        preferred_parent = self.mote.rpl.getPreferredParent()

        # collect TX cells which has enough numTX
        tx_cell_list = [cell for cell in self.mote.tsch.get_cells(preferred_parent, self.SLOTFRAME_HANDLE_NEGOTIATED_CELLS) if cell.options == [d.CELLOPTION_TX]]
        # pick up TX cells whose NumTx is larger than
        # MSF_MIN_NUM_TX. This is an implementation decision, which is
        # easier to implement than what section 5.3 of
        # draft-ietf-6tisch-msf-03.txt describes as the step-2 of the
        # house-keeping process.
        tx_cell_list = {
            cell.slot_offset: cell for cell in tx_cell_list if (
                d.MSF_MIN_NUM_TX < cell.num_tx
            )
        }
        # collect PDRs of the TX cells
        def pdr(cell):
            assert cell.num_tx > 0
            return cell.num_tx_ack / float(cell.num_tx)
        pdr_list = {
            slotOffset: pdr(cell) for slotOffset, cell in list(tx_cell_list.items())
        }

        if len(pdr_list) > 0:
            # find a cell to relocate using the highest PDR value
            highest_pdr = max(pdr_list.values())
            relocation_cell_list = [
                {
                    'slotOffset'   : slotOffset,
                    'channelOffset': tx_cell_list[slotOffset].channel_offset
                } for slotOffset, pdr in list(pdr_list.items()) if (
                    d.MSF_RELOCATE_PDRTHRES < (highest_pdr - pdr)
                )
            ]
            if (
                    len(relocation_cell_list) > 0
                    and
                    self.retry_count[preferred_parent] == -1
                ):
                # reset retry counter
                self.retry_count[preferred_parent] = 0
                self._request_relocating_cells(
                    neighbor             = preferred_parent,
                    cell_options         = self.TX_CELL_OPT,
                    num_relocating_cells = len(relocation_cell_list),
                    cell_list            = relocation_cell_list
                )
        else:
            # we don't have any TX cell whose PDR is available; do nothing
            pass

        # schedule next housekeeping
        self.engine.scheduleIn(
            delay         = d.MSF_HOUSEKEEPINGCOLLISION_PERIOD,
            cb            = self._housekeeping_collision,
            uniqueTag     = (self.mote.id, u'_housekeeping_collision'),
            intraSlotOrder= d.INTRASLOTORDER_STACKTASKS,
        )

    # cell manipulation helpers
    def _lock_cells(self, cell_list):
        for cell in cell_list:
            self.locked_slots.add(cell[u'slotOffset'])

    def _unlock_cells(self, cell_list):
        for cell in cell_list:
            self.locked_slots.remove(cell[u'slotOffset'])

    


    def _add_cells(self, neighbor, cell_list, cell_options):
        try:
            
            ss=self.select_slot_frame(1)
            # print(cell_list)
            gg=self.select_ch(ss)
            for cell in cell_list:
                # print(cell[u'slotOffset'])
                # print(cell[u'channelOffset'])
                print(9) 
                # RTEW=RTEW+1
                self.mote.tsch.addCell(
                    slotOffset         = cell[u'slotOffset'],
                    channelOffset      = cell[u'channelOffset'],
                    neighbor           = neighbor,
                    cellOptions        = cell_options,
                    slotframe_handle   = self.SLOTFRAME_HANDLE_NEGOTIATED_CELLS
                )
                print("SDSDSDSSDSDSDSDSDSD")
                
            if (
                    cell_options == [d.CELLOPTION_TX]
                    and
                    self.get_autonomous_tx_cell(neighbor)
                ):
                self.deallocate_autonomous_tx_cell(neighbor)
        except Exception:
            # We may fail in adding cells since they could be allocated for
            # another peer. We need to have a locking or reservation mechanism
            # to avoid such a situation.
            raise

    def select_slot_frame(self,n):
        # making assumption of first slot frame offset to be 5
        # if Fis == 0:
            # Fis == 1 # global variable to mark for first output
        # time.sleep(0.5)
        GI=self.L # Get all the available slots
        G=GI[:]
        G.pop(0) # Remove 0
        G.pop(0)

        # we have something like 1 1 2 2 3 3 .... n-1 n-1
        taken_length=len(self.taken)
        
        s=0
        print(G)
        print("ABOVE IS taken SEND")
        print(self.taken)
        print("ABOVE IS taken SEND")
        busy=[]
        if len(self.taken)==56:
            del self.taken[:]
        
        for j in self.taken:
            flag=0
            s=0
            for i in G:
                if i == j:
                    G.pop(s)
                    # busy.append(s)
                    s=s+1
                    flag=flag+1
                else:
                    s=s+1
                if flag==1:
                    break

                
        # print(busy)
        # print("xxxxxxxxxxxxxxxxxx")
        # print(G[0])
        # print(G[1])
        # # G.pop(0)
        # # G.pop(0)
        # print(len(busy))
        # if len(busy)==50:
        #     busy=[]
        #     del self.taken[:]
        # for e in busy:
        #     G.pop(0)
        print(G)
        print("xxxxxxxxxxxxxxxxxx")
        # remove all those which are taken
        num_slot=n
        if self.hops == 1:
            num_slot=num_slot+1
        else:
            num_slot=num_slot
        
        self.taken.append(G[0])
        consecutive=[]
        s=0
        num_slot=1
        for i in range(num_slot):
            consecutive.append(G[s])
            s=s+1
        # Now we have the best possible available slot at 0th
        print(consecutive)
        print("ABOVE IS LIST SEND")
        
        # take the smallest one
        # E=self.por
        # print(G)
        # s=E[0]
        # self.por.pop(0)
        # print(s)
        # print(G[0])
        print("------x-x-x-x-x-x-x-x--x-x-x-------")
        # return s
        
        return consecutive[0]

    def select_ch(self,fs):
        # making assumption of first slot frame offset to be 5
        # if Fis == 0:
            # Fis == 1 # global variable to mark for first output
        # time.sleep(0.5)
        s=4
        if fs == 1:
            G=self.S4[:] # Get all the channel offsets of the flow fs
            # make a taken array
            # s=G[0]
            # self.S4.pop(0)
            H=self.takenS4
            busy=[]
            for j in H:
                p=0
                flag=0
                for i in G:
                    if i == j:
                        # G.pop(s)
                        busy.append(p)
                        p=p+1
                        flag=flag+1
                    else:
                        p=p+1
                    if flag==1:
                        break
            for e in busy:
                G.pop(0)
            self.takenS4.append(G[0])
            s=G[0]

        if fs == 2:
            G=self.S4[:] # Get all the channel offsets of the flow fs
            # make a taken array
            # s=G[0]
            # self.S4.pop(0)
            H=self.takenS5
            busy=[]
            for j in H:
                p=0
                flag=0
                for i in G:
                    if i == j:
                        # G.pop(s)
                        busy.append(p)
                        p=p+1
                        flag=flag+1
                    else:
                        p=p+1
                    if flag==1:
                        break
            for e in busy:
                G.pop(0)
            self.takenS5.append(G[0])
            s=G[0]
        if fs == 3:
            G=self.S5[:] # Get all the channel offsets of the flow fs
            # make a taken array
            # s=G[0]
            # self.S4.pop(0)
            H=self.takenS6
            busy=[]
            for j in H:
                p=0
                flag=0
                for i in G:
                    if i == j:
                        # G.pop(s)
                        busy.append(p)
                        p=p+1
                        flag=flag+1
                    else:
                        p=p+1
                    if flag==1:
                        break
            for e in busy:
                G.pop(0)
            self.takenS6.append(G[0])
            s=G[0]
        if fs == 4:
            G=self.S5[:] # Get all the channel offsets of the flow fs
            # make a taken array
            # s=G[0]
            # self.S4.pop(0)
            H=self.takenS7
            busy=[]
            for j in H:
                p=0
                flag=0
                for i in G:
                    if i == j:
                        # G.pop(s)
                        busy.append(p)
                        p=p+1
                        flag=flag+1
                    else:
                        p=p+1
                    if flag==1:
                        break
            for e in busy:
                G.pop(0)
            self.takenS7.append(G[0])
            s=G[0]
        if fs == 5:
            G=self.S5[:] # Get all the channel offsets of the flow fs
            # make a taken array
            # s=G[0]
            # self.S4.pop(0)
            H=self.takenS8
            busy=[]
            for j in H:
                p=0
                flag=0
                for i in G:
                    if i == j:
                        # G.pop(s)
                        busy.append(p)
                        p=p+1
                        flag=flag+1
                    else:
                        p=p+1
                    if flag==1:
                        break
            for e in busy:
                G.pop(0)
            self.takenS8.append(G[0])
            s=G[0]
        if fs == 6:
            G=self.S5[:] # Get all the channel offsets of the flow fs
            # make a taken array
            # s=G[0]
            # self.S4.pop(0)
            H=self.takenS9
            busy=[]
            for j in H:
                p=0
                flag=0
                for i in G:
                    if i == j:
                        # G.pop(s)
                        busy.append(p)
                        p=p+1
                        flag=flag+1
                    else:
                        p=p+1
                    if flag==1:
                        break
            for e in busy:
                G.pop(0)
            self.takenS9.append(G[0])
            s=G[0]
        if fs == 7:
            G=self.S5[:] # Get all the channel offsets of the flow fs
            # make a taken array
            # s=G[0]
            # self.S4.pop(0)
            H=self.takenS26
            busy=[]
            for j in H:
                p=0
                flag=0
                for i in G:
                    if i == j:
                        # G.pop(s)
                        busy.append(p)
                        p=p+1
                        flag=flag+1
                    else:
                        p=p+1
                    if flag==1:
                        break
            for e in busy:
                G.pop(0)
            self.takenS26.append(G[0])
            s=G[0]
        if fs == 8:
            G=self.S5[:] # Get all the channel offsets of the flow fs
            # make a taken array
            # s=G[0]
            # self.S4.pop(0)
            H=self.takenS10
            busy=[]
            for j in H:
                p=0
                flag=0
                for i in G:
                    if i == j:
                        # G.pop(s)
                        busy.append(p)
                        p=p+1
                        flag=flag+1
                    else:
                        p=p+1
                    if flag==1:
                        break
            for e in busy:
                G.pop(0)
            self.takenS10.append(G[0])
            s=G[0]
        if fs == 9:
            G=self.S5[:] # Get all the channel offsets of the flow fs
            # make a taken array
            # s=G[0]
            # self.S4.pop(0)
            H=self.takenS11
            busy=[]
            for j in H:
                p=0
                flag=0
                for i in G:
                    if i == j:
                        # G.pop(s)
                        busy.append(p)
                        p=p+1
                        flag=flag+1
                    else:
                        p=p+1
                    if flag==1:
                        break
            for e in busy:
                G.pop(0)
            self.takenS11.append(G[0])
            s=G[0]
        if fs == 10:
            G=self.S5[:] # Get all the channel offsets of the flow fs
            # make a taken array
            # s=G[0]
            # self.S4.pop(0)
            H=self.takenS12
            busy=[]
            for j in H:
                p=0
                flag=0
                for i in G:
                    if i == j:
                        # G.pop(s)
                        busy.append(p)
                        p=p+1
                        flag=flag+1
                    else:
                        p=p+1
                    if flag==1:
                        break
            for e in busy:
                G.pop(0)
            self.takenS12.append(G[0])
            s=G[0]
        if fs == 11:
            G=self.S5[:] # Get all the channel offsets of the flow fs
            # make a taken array
            # s=G[0]
            # self.S4.pop(0)
            H=self.takenS13
            busy=[]
            for j in H:
                p=0
                flag=0
                for i in G:
                    if i == j:
                        # G.pop(s)
                        busy.append(p)
                        p=p+1
                        flag=flag+1
                    else:
                        p=p+1
                    if flag==1:
                        break
            for e in busy:
                G.pop(0)
            self.takenS13.append(G[0])
            s=G[0]
        if fs == 12:
            G=self.S5[:] # Get all the channel offsets of the flow fs
            # make a taken array
            # s=G[0]
            # self.S4.pop(0)
            H=self.takenS14
            busy=[]
            for j in H:
                p=0
                flag=0
                for i in G:
                    if i == j:
                        # G.pop(s)
                        busy.append(p)
                        p=p+1
                        flag=flag+1
                    else:
                        p=p+1
                    if flag==1:
                        break
            for e in busy:
                G.pop(0)
            self.takenS14.append(G[0])
            s=G[0]
        if fs == 13:
            G=self.S5[:] # Get all the channel offsets of the flow fs
            # make a taken array
            # s=G[0]
            # self.S4.pop(0)
            H=self.takenS15
            busy=[]
            for j in H:
                p=0
                flag=0
                for i in G:
                    if i == j:
                        # G.pop(s)
                        busy.append(p)
                        p=p+1
                        flag=flag+1
                    else:
                        p=p+1
                    if flag==1:
                        break
            for e in busy:
                G.pop(0)
            self.takenS15.append(G[0])
            s=G[0]
        if fs == 14:
            G=self.S5[:] # Get all the channel offsets of the flow fs
            # make a taken array
            # s=G[0]
            # self.S4.pop(0)
            H=self.takenS16
            busy=[]
            for j in H:
                p=0
                flag=0
                for i in G:
                    if i == j:
                        # G.pop(s)
                        busy.append(p)
                        p=p+1
                        flag=flag+1
                    else:
                        p=p+1
                    if flag==1:
                        break
            for e in busy:
                G.pop(0)
            self.takenS16.append(G[0])
            s=G[0]
        if fs == 15:
            G=self.S5[:] # Get all the channel offsets of the flow fs
            # make a taken array
            # s=G[0]
            # self.S4.pop(0)
            H=self.takenS17
            busy=[]
            for j in H:
                p=0
                flag=0
                for i in G:
                    if i == j:
                        # G.pop(s)
                        busy.append(p)
                        p=p+1
                        flag=flag+1
                    else:
                        p=p+1
                    if flag==1:
                        break
            for e in busy:
                G.pop(0)
            self.takenS17.append(G[0])
            s=G[0]
        if fs == 16:
            G=self.S5[:] # Get all the channel offsets of the flow fs
            # make a taken array
            # s=G[0]
            # self.S4.pop(0)
            H=self.takenS18
            busy=[]
            for j in H:
                p=0
                flag=0
                for i in G:
                    if i == j:
                        # G.pop(s)
                        busy.append(p)
                        p=p+1
                        flag=flag+1
                    else:
                        p=p+1
                    if flag==1:
                        break
            for e in busy:
                G.pop(0)
            self.takenS18.append(G[0])
            s=G[0]
        if fs == 17:
            G=self.S5[:] # Get all the channel offsets of the flow fs
            # make a taken array
            # s=G[0]
            # self.S4.pop(0)
            H=self.takenS27
            busy=[]
            for j in H:
                p=0
                flag=0
                for i in G:
                    if i == j:
                        # G.pop(s)
                        busy.append(p)
                        p=p+1
                        flag=flag+1
                    else:
                        p=p+1
                    if flag==1:
                        break
            for e in busy:
                G.pop(0)
            self.takenS27.append(G[0])
            s=G[0]
        if fs == 18:
            G=self.S5[:] # Get all the channel offsets of the flow fs
            # make a taken array
            # s=G[0]
            # self.S4.pop(0)
            H=self.takenS28
            busy=[]
            for j in H:
                p=0
                flag=0
                for i in G:
                    if i == j:
                        # G.pop(s)
                        busy.append(p)
                        p=p+1
                        flag=flag+1
                    else:
                        p=p+1
                    if flag==1:
                        break
            for e in busy:
                G.pop(0)
            self.takenS28.append(G[0])
            s=G[0]
        if fs == 19:
            G=self.S5[:] # Get all the channel offsets of the flow fs
            # make a taken array
            # s=G[0]
            # self.S4.pop(0)
            H=self.takenS19
            busy=[]
            for j in H:
                p=0
                flag=0
                for i in G:
                    if i == j:
                        # G.pop(s)
                        busy.append(p)
                        p=p+1
                        flag=flag+1
                    else:
                        p=p+1
                    if flag==1:
                        break
            for e in busy:
                G.pop(0)
            self.takenS19.append(G[0])
            s=G[0]
        if fs == 20:
            G=self.S5[:] # Get all the channel offsets of the flow fs
            # make a taken array
            # s=G[0]
            # self.S4.pop(0)
            H=self.takenS20
            busy=[]
            for j in H:
                p=0
                flag=0
                for i in G:
                    if i == j:
                        # G.pop(s)
                        busy.append(p)
                        p=p+1
                        flag=flag+1
                    else:
                        p=p+1
                    if flag==1:
                        break
            for e in busy:
                G.pop(0)
            self.takenS20.append(G[0])
            s=G[0]
        if fs == 21:
            G=self.S5[:] # Get all the channel offsets of the flow fs
            # make a taken array
            # s=G[0]
            # self.S4.pop(0)
            H=self.takenS21
            busy=[]
            for j in H:
                p=0
                flag=0
                for i in G:
                    if i == j:
                        # G.pop(s)
                        busy.append(p)
                        p=p+1
                        flag=flag+1
                    else:
                        p=p+1
                    if flag==1:
                        break
            for e in busy:
                G.pop(0)
            self.takenS21.append(G[0])
            s=G[0]
        if fs == 22:
            G=self.S5[:] # Get all the channel offsets of the flow fs
            # make a taken array
            # s=G[0]
            # self.S4.pop(0)
            H=self.takenS22
            busy=[]
            for j in H:
                p=0
                flag=0
                for i in G:
                    if i == j:
                        # G.pop(s)
                        busy.append(p)
                        p=p+1
                        flag=flag+1
                    else:
                        p=p+1
                    if flag==1:
                        break
            for e in busy:
                G.pop(0)
            self.takenS22.append(G[0])
            s=G[0]
        if fs == 23:
            G=self.S5[:] # Get all the channel offsets of the flow fs
            # make a taken array
            # s=G[0]
            # self.S4.pop(0)
            H=self.takenS23
            busy=[]
            for j in H:
                p=0
                flag=0
                for i in G:
                    if i == j:
                        # G.pop(s)
                        busy.append(p)
                        p=p+1
                        flag=flag+1
                    else:
                        p=p+1
                    if flag==1:
                        break
            for e in busy:
                G.pop(0)
            self.takenS23.append(G[0])
            s=G[0]
        if fs == 24:
            G=self.S5[:] # Get all the channel offsets of the flow fs
            # make a taken array
            # s=G[0]
            # self.S4.pop(0)
            H=self.takenS24
            busy=[]
            for j in H:
                p=0
                flag=0
                for i in G:
                    if i == j:
                        # G.pop(s)
                        busy.append(p)
                        p=p+1
                        flag=flag+1
                    else:
                        p=p+1
                    if flag==1:
                        break
            for e in busy:
                G.pop(0)
            self.takenS24.append(G[0])
            s=G[0]
        if fs == 25:
            G=self.S5[:] # Get all the channel offsets of the flow fs
            # make a taken array
            # s=G[0]
            # self.S4.pop(0)
            H=self.takenS25
            busy=[]
            for j in H:
                p=0
                flag=0
                for i in G:
                    if i == j:
                        # G.pop(s)
                        busy.append(p)
                        p=p+1
                        flag=flag+1
                    else:
                        p=p+1
                    if flag==1:
                        break
            for e in busy:
                G.pop(0)
            self.takenS25.append(G[0])
            s=G[0]
        if fs == 26:
            G=self.S5[:] # Get all the channel offsets of the flow fs
            # make a taken array
            # s=G[0]
            # self.S4.pop(0)
            H=self.takenS29
            busy=[]
            for j in H:
                p=0
                flag=0
                for i in G:
                    if i == j:
                        # G.pop(s)
                        busy.append(p)
                        p=p+1
                        flag=flag+1
                    else:
                        p=p+1
                    if flag==1:
                        break
            for e in busy:
                G.pop(0)
            self.takenS29.append(G[0])
            s=G[0]
        if fs == 27:
            G=self.S5[:] # Get all the channel offsets of the flow fs
            # make a taken array
            # s=G[0]
            # self.S4.pop(0)
            H=self.takenS30
            busy=[]
            for j in H:
                p=0
                flag=0
                for i in G:
                    if i == j:
                        # G.pop(s)
                        busy.append(p)
                        p=p+1
                        flag=flag+1
                    else:
                        p=p+1
                    if flag==1:
                        break
            for e in busy:
                G.pop(0)
            self.takenS30.append(G[0])
            s=G[0]
        if fs == 28:
            G=self.S5[:] # Get all the channel offsets of the flow fs
            # make a taken array
            # s=G[0]
            # self.S4.pop(0)
            H=self.takenS31
            busy=[]
            for j in H:
                p=0
                flag=0
                for i in G:
                    if i == j:
                        # G.pop(s)
                        busy.append(p)
                        p=p+1
                        flag=flag+1
                    else:
                        p=p+1
                    if flag==1:
                        break
            for e in busy:
                G.pop(0)
            self.takenS31.append(G[0])
            s=G[0]
        
        return s

    def _delete_cells(self, neighbor, cell_list, cell_options):
        for cell in cell_list:
            print(cell[u'slotOffset'])
            print("----------")
            if self.mote.tsch.get_cell(
                    slot_offset      = cell[u'slotOffset'],
                    channel_offset   = cell[u'channelOffset'],
                    mac_addr         = neighbor,
                    slotframe_handle = self.SLOTFRAME_HANDLE_NEGOTIATED_CELLS
               ) is None:
                # the cell may have been deleted for some reason
                continue
            self.mote.tsch.deleteCell(
                slotOffset       = cell[u'slotOffset'],
                channelOffset    = cell[u'channelOffset'],
                neighbor         = neighbor,
                cellOptions      = cell_options,
                slotframe_handle = self.SLOTFRAME_HANDLE_NEGOTIATED_CELLS
            )

    def _clear_cells(self, neighbor):
        cells = self.mote.tsch.get_cells(
            neighbor,
            self.SLOTFRAME_HANDLE_NEGOTIATED_CELLS
        )
        for cell in cells:
            assert neighbor == cell.mac_addr
            assert d.CELLOPTION_SHARED not in cell.options
            self.mote.tsch.deleteCell(
                slotOffset       = cell.slot_offset,
                channelOffset    = cell.channel_offset,
                neighbor         = cell.mac_addr,
                cellOptions      = cell.options,
                slotframe_handle = self.SLOTFRAME_HANDLE_NEGOTIATED_CELLS
            )
        self.mote.sixp.reset_seqnum(neighbor)

    def _relocate_cells(
            self,
            neighbor,
            src_cell_list,
            dst_cell_list,
            cell_options
        ):
        if not dst_cell_list:
            return

        assert len(src_cell_list) == len(dst_cell_list)
        # relocation
        print(dst_cell_list)
        print('s')
        print(src_cell_list)
        print('s')
        self._add_cells(neighbor, dst_cell_list, cell_options)
        self._delete_cells(neighbor, src_cell_list, cell_options)

    def _get_available_slots(self):
        return list(
            set(self.mote.tsch.get_available_slots(self.SLOTFRAME_HANDLE_NEGOTIATED_CELLS)) -
            self.locked_slots
        )

    def _create_available_cell_list(self, cell_list_len):
        available_slots = self._get_available_slots()
        # remove slot offset 0 that is reserved for the minimal shared
        # cell
        if 0 in available_slots:
            available_slots.remove(0)

        # remove the slot offset used for the autonomous RX cell
        autonomous_rx_cell = self.get_autonomous_rx_cell()
        assert autonomous_rx_cell
        if autonomous_rx_cell.slot_offset in available_slots:
            available_slots.remove(autonomous_rx_cell.slot_offset)

        if len(available_slots) < cell_list_len:
            # we don't have enough available cells; no cell is selected
            selected_slots = []
        else:
            selected_slots = random.sample(available_slots, cell_list_len)

        cell_list = []
        for slot_offset in selected_slots:
            channel_offset = random.randint(0, self.settings.phy_numChans - 1)
            cell_list.append(
                {
                    'slotOffset'   : slot_offset,
                    'channelOffset': channel_offset
                }
            )
        self._lock_cells(cell_list)
        return cell_list

    def _create_occupied_cell_list(
            self,
            neighbor,
            cell_options,
            cell_list_len
        ):

        occupied_cells = [cell for cell in self.mote.tsch.get_cells(neighbor, self.SLOTFRAME_HANDLE_NEGOTIATED_CELLS) if cell.options == cell_options]

        cell_list = [
            {
                'slotOffset'   : cell.slot_offset,
                'channelOffset': cell.channel_offset
            } for cell in occupied_cells
        ]

        if cell_list_len <= len(occupied_cells):
            cell_list = random.sample(cell_list, cell_list_len)

        return cell_list

    def _are_cells_allocated(
            self,
            peerMac,
            cell_list,
            cell_options
        ):

        # collect allocated cells
        assert cell_options in [self.TX_CELL_OPT, self.RX_CELL_OPT]
        allocated_cells = [cell for cell in self.mote.tsch.get_cells(peerMac, self.SLOTFRAME_HANDLE_NEGOTIATED_CELLS) if cell.options == cell_options]

        # test all the cells in the cell list against the allocated cells
        ret_val = True
        for cell in cell_list:
            slotOffset    = cell[u'slotOffset']
            channelOffset = cell[u'channelOffset']
            cell = self.mote.tsch.get_cell(
                slot_offset      = slotOffset,
                channel_offset   = channelOffset,
                mac_addr         = peerMac,
                slotframe_handle = self.SLOTFRAME_HANDLE_NEGOTIATED_CELLS
            )

            if cell is None:
                ret_val = False
                break

        return ret_val

    # ADD command related stuff
    def _request_adding_cells(
            self,
            neighbor,
            num_tx_cells   = 0,
            num_rx_cells   = 0
        ):

        # determine num_cells and cell_options; update num_{tx,rx}_cells
        if num_tx_cells > 0:
            cell_options = self.TX_CELL_OPT
            if num_tx_cells < self.DEFAULT_CELL_LIST_LEN:
                num_cells    = num_tx_cells
                num_tx_cells = 0
            else:
                num_cells    = self.DEFAULT_CELL_LIST_LEN
                num_tx_cells = num_tx_cells - self.DEFAULT_CELL_LIST_LEN
        elif num_rx_cells > 0:
            cell_options = self.RX_CELL_OPT
            num_cells    = num_rx_cells
            if num_rx_cells < self.DEFAULT_CELL_LIST_LEN:
                num_cells    = num_rx_cells
                num_rx_cells = 0
            else:
                num_cells    = self.DEFAULT_CELL_LIST_LEN
                num_rx_cells = num_rx_cells - self.DEFAULT_CELL_LIST_LEN
        else:
            # nothing to add
            self.retry_count[neighbor] = -1
            return

        # prepare cell_list
        cell_list = self._create_available_cell_list(self.DEFAULT_CELL_LIST_LEN)

        if len(cell_list) == 0:
            # we don't have available cells right now
            self.log(
                SimEngine.SimLog.LOG_MSF_ERROR_SCHEDULE_FULL,
                {
                    '_mote_id'    : self.mote.id
                }
            )
            self.retry_count[neighbor] = -1
            return

        # prepare _callback which is passed to SixP.send_request()
        callback = self._create_add_request_callback(
            neighbor,
            num_cells,
            cell_options,
            cell_list,
            num_tx_cells,
            num_rx_cells
        )

        # send a request
        self.mote.sixp.send_request(
            dstMac      = neighbor,
            command     = d.SIXP_CMD_ADD,
            cellOptions = cell_options,
            numCells    = num_cells,
            cellList    = cell_list,
            callback    = callback
        )

    def _receive_add_request(self, request):

        # for quick access
        proposed_cells = request[u'app'][u'cellList']
        peerMac         = request[u'mac'][u'srcMac']
         # This is the part where we get the avaiable slots
         # proposed_cells is the part which is given the random values for neogtiated cells


        # find available cells in the received CellList
        slots_in_cell_list = set(
            [c[u'slotOffset'] for c in proposed_cells]
        )
        available_slots  = list(
            slots_in_cell_list.intersection(
                set(self._get_available_slots())
            )
        )
        slotframe = self.mote.tsch.get_slotframe(
            1
        )
       
        print(slotframe)
        print("D")

        # prepare cell_list
        candidate_cells = [
            c for c in proposed_cells if c[u'slotOffset'] in available_slots
        ]
        if len(candidate_cells) < request[u'app'][u'numCells']:
            cell_list = candidate_cells
        else:
            cell_list = random.sample(
                candidate_cells,
                request[u'app'][u'numCells']
            )

        # prepare callback
        if len(available_slots) > 0:
            code = d.SIXP_RC_SUCCESS

            self._lock_cells(candidate_cells)
            def callback(event, packet):
                print(request)
                print('E')
                if event == d.SIXP_CALLBACK_EVENT_MAC_ACK_RECEPTION:
                    # prepare cell options for this responder
                    if request[u'app'][u'cellOptions'] == self.TX_CELL_OPT:
                        # invert direction
                        cell_options = self.RX_CELL_OPT
                    elif request[u'app'][u'cellOptions'] == self.RX_CELL_OPT:
                        # invert direction
                        cell_options = self.TX_CELL_OPT
                    else:
                        # Unsupported cell options for MSF
                        raise Exception()
                    # print(cell_list)
                    # print('d')
                
                    self._add_cells(
                        neighbor     = peerMac,
                        cell_list    = cell_list,
                        cell_options = cell_options
                )
                self._unlock_cells(candidate_cells)
        else:
            code      = d.SIXP_RC_ERR
            cell_list = None
            callback  = None

        # send a response
        self.mote.sixp.send_response(
            dstMac      = peerMac,
            return_code = code,
            cellList    = cell_list,
            callback    = callback
        )

    def _create_add_request_callback(
            self,
            neighbor,
            num_cells,
            cell_options,
            cell_list,
            num_tx_cells,
            num_rx_cells
        ):
        def callback(event, packet):
            if event == d.SIXP_CALLBACK_EVENT_PACKET_RECEPTION:
                assert packet[u'app'][u'msgType'] == d.SIXP_MSG_TYPE_RESPONSE
                if packet[u'app'][u'code'] == d.SIXP_RC_SUCCESS:
                    # add cells on success of the transaction
                    # print(packet[u'app'][u'cellList'])
                    # print('e')
                    self._add_cells(
                        neighbor     = neighbor,
                        cell_list    = packet[u'app'][u'cellList'],
                        cell_options = cell_options
                    )

                    # The received CellList could be smaller than the requested
                    # NumCells; adjust num_{tx,rx}_cells
                    _num_tx_cells   = num_tx_cells
                    _num_rx_cells   = num_rx_cells
                    remaining_cells = num_cells - len(packet[u'app'][u'cellList'])
                    if remaining_cells > 0:
                        if cell_options == self.TX_CELL_OPT:
                            _num_tx_cells -= remaining_cells
                        elif cell_options == self.RX_CELL_OPT:
                            _num_rx_cells -= remaining_cells
                        else:
                            # never comes here
                            raise Exception()

                    # start another transaction
                    self.retry_count[neighbor] = 0
                    self._request_adding_cells(
                        neighbor       = neighbor,
                        num_tx_cells   = _num_tx_cells,
                        num_rx_cells   = _num_rx_cells
                    )
                else:
                    # TODO: request doesn't succeed; how should we do?
                    self.retry_count[neighbor] = -1

            elif event == d.SIXP_CALLBACK_EVENT_TIMEOUT:
                if self.retry_count[neighbor] == self.MAX_RETRY:
                    # give up this neighbor
                    if neighbor == self.mote.rpl.getPreferredParent():
                        self.mote.rpl.of.poison_rpl_parent(neighbor)
                    self.retry_count[neighbor] = -1 # done
                else:
                    # retry
                    self.retry_count[neighbor] += 1
                    if cell_options == self.TX_CELL_OPT:
                        _num_tx_cells = num_cells + num_tx_cells
                        _num_rx_cells = num_rx_cells
                    else:
                        _num_tx_cells = num_tx_cells
                        _num_rx_cells = num_cells + num_rx_cells
                    self._request_adding_cells(
                        neighbor       = neighbor,
                        num_tx_cells   = _num_tx_cells,
                        num_rx_cells   = _num_rx_cells
                    )
            else:
                # ignore other events
                pass

            # unlock the slots used in this transaction
            self._unlock_cells(cell_list)

        return callback

    # DELETE command related stuff
    def _request_deleting_cells(
            self,
            neighbor,
            num_cells,
            cell_options
        ):

        # prepare cell_list to send
        cell_list = self._create_occupied_cell_list(
            neighbor      = neighbor,
            cell_options  = cell_options,
            cell_list_len = self.DEFAULT_CELL_LIST_LEN
        )
        assert len(cell_list) > 0

        # prepare callback
        callback = self._create_delete_request_callback(
            neighbor,
            num_cells,
            cell_options
        )

        # send a DELETE request
        self.mote.sixp.send_request(
            dstMac      = neighbor,
            command     = d.SIXP_CMD_DELETE,
            cellOptions = cell_options,
            numCells    = num_cells,
            cellList    = cell_list,
            callback    = callback
        )

    def _receive_delete_request(self, request):
        # for quick access
        num_cells           = request[u'app'][u'numCells']
        cell_options        = request[u'app'][u'cellOptions']
        candidate_cell_list = request[u'app'][u'cellList']
        peerMac             = request[u'mac'][u'srcMac']

        # confirm all the cells in the cell list are allocated for the peer
        # with the specified cell options
        #
        # invert the direction in cell_options
        assert cell_options in [self.TX_CELL_OPT, self.RX_CELL_OPT]
        if   cell_options == self.TX_CELL_OPT:
            our_cell_options = self.RX_CELL_OPT
        elif cell_options == self.RX_CELL_OPT:
            our_cell_options   = self.TX_CELL_OPT

        if (
                (
                    self._are_cells_allocated(
                        peerMac      = peerMac,
                        cell_list    = candidate_cell_list,
                        cell_options = our_cell_options
                    ) is True
                )
                and
                (num_cells <= len(candidate_cell_list))
            ):
            code = d.SIXP_RC_SUCCESS
            cell_list = random.sample(candidate_cell_list, num_cells)

            def callback(event, packet):
                if event == d.SIXP_CALLBACK_EVENT_MAC_ACK_RECEPTION:
                    self._delete_cells(
                        neighbor     = peerMac,
                        cell_list    = cell_list,
                        cell_options = our_cell_options
                )
        else:
            code      = d.SIXP_RC_ERR
            cell_list = None
            callback  = None

        # send the response
        self.mote.sixp.send_response(
            dstMac      = peerMac,
            return_code = code,
            cellList    = cell_list,
            callback    = callback
        )

    def _create_delete_request_callback(
            self,
            neighbor,
            num_cells,
            cell_options
        ):
        def callback(event, packet):
            if (
                    (event == d.SIXP_CALLBACK_EVENT_PACKET_RECEPTION)
                    and
                    (packet[u'app'][u'msgType'] == d.SIXP_MSG_TYPE_RESPONSE)
                ):
                self.retry_count[neighbor] = -1
                if packet[u'app'][u'code'] == d.SIXP_RC_SUCCESS:
                    self._delete_cells(
                        neighbor     = neighbor,
                        cell_list    = packet[u'app'][u'cellList'],
                        cell_options = cell_options
                    )
                else:
                    # TODO: request doesn't succeed; how should we do?
                    pass
            elif event == d.SIXP_CALLBACK_EVENT_TIMEOUT:
                if self.retry_count[neighbor] == self.MAX_RETRY:
                    # give it up
                    self.retry_count[neighbor] = -1
                    if neighbor == self.mote.rpl.getPreferredParent():
                        self.mote.rpl.of.poison_rpl_parent(neighbor)
                else:
                    # retry
                    self.retry_count[neighbor] += 1
                    self._request_deleting_cells(
                        neighbor,
                        num_cells,
                        cell_options
                    )
            else:
                # ignore other events
                pass

        return callback

    # RELOCATE command related stuff
    def _request_relocating_cells(
            self,
            neighbor,
            cell_options,
            num_relocating_cells,
            cell_list
        ):

        # determine num_cells and relocation_cell_list;
        # update num_relocating_cells and cell_list
        if self.DEFAULT_CELL_LIST_LEN < num_relocating_cells:
            num_cells             = self.DEFAULT_CELL_LIST_LEN
            relocation_cell_list  = cell_list[:self.DEFAULT_CELL_LIST_LEN]
            num_relocating_cells -= self.DEFAULT_CELL_LIST_LEN
            cell_list             = cell_list[self.DEFAULT_CELL_LIST_LEN:]
        else:
            num_cells             = num_relocating_cells
            relocation_cell_list  = cell_list
            num_relocating_cells  = 0
            cell_list             = []

        # we don't have any cell to relocate; done
        if len(relocation_cell_list) == 0:
            self.retry_count[neighbor] = -1
            return

        # prepare candidate_cell_list
        candidate_cell_list = self._create_available_cell_list(
            self.DEFAULT_CELL_LIST_LEN
        )

        if len(candidate_cell_list) == 0:
            # no available cell to move the cells to
            self.log(
                SimEngine.SimLog.LOG_MSF_ERROR_SCHEDULE_FULL,
                {
                    '_mote_id'    : self.mote.id
                }
            )
            self.retry_count[neighbor] = -1
            return

        # prepare callback
        def callback(event, packet):
            if event == d.SIXP_CALLBACK_EVENT_PACKET_RECEPTION:
                assert packet[u'app'][u'msgType'] == d.SIXP_MSG_TYPE_RESPONSE
                if packet[u'app'][u'code'] == d.SIXP_RC_SUCCESS:
                    # perform relocations
                    num_relocations = len(packet[u'app'][u'cellList'])
                    self._relocate_cells(
                        neighbor      = neighbor,
                        src_cell_list = relocation_cell_list[:num_cells],
                        dst_cell_list = packet[u'app'][u'cellList'],
                        cell_options  = cell_options
                    )

                    # adjust num_relocating_cells and cell_list
                    _num_relocating_cells = (
                        num_relocating_cells + num_cells - num_relocations
                    )
                    _cell_list = (
                        cell_list + relocation_cell_list[num_relocations:]
                    )

                    # start another transaction
                    self.retry_count[neighbor] = 0
                    self._request_relocating_cells(
                        neighbor             = neighbor,
                        cell_options         = cell_options,
                        num_relocating_cells = _num_relocating_cells,
                        cell_list            = _cell_list
                    )
            elif event == d.SIXP_CALLBACK_EVENT_TIMEOUT:
                if self.retry_count[neighbor] == self.MAX_RETRY:
                    # give up this neighbor
                    if neighbor == self.mote.rpl.getPreferredParent():
                        self.mote.rpl.of.poison_rpl_parent(neighbor)
                    self.retry_count[neighbor] = -1 # done
                else:
                    # retry
                    self.retry_count[neighbor] += 1
                    self._request_relocating_cells(
                        neighbor,
                        cell_options,
                        num_relocating_cells,
                        cell_list
                    )

            # unlock the slots used in this transaction
            self._unlock_cells(candidate_cell_list)

        # send a request
        self.mote.sixp.send_request(
            dstMac             = neighbor,
            command            = d.SIXP_CMD_RELOCATE,
            cellOptions        = cell_options,
            numCells           = num_cells,
            relocationCellList = relocation_cell_list,
            candidateCellList  = candidate_cell_list,
            callback           = callback
        )

    def _receive_relocate_request(self, request):
        # for quick access
        num_cells        = request[u'app'][u'numCells']
        cell_options     = request[u'app'][u'cellOptions']
        relocating_cells = request[u'app'][u'relocationCellList']
        candidate_cells  = request[u'app'][u'candidateCellList']
        peerMac          = request[u'mac'][u'srcMac']

        # confirm all the cells in the cell list are allocated for the peer
        # with the specified cell options
        #
        # invert the direction in cell_options
        assert cell_options in [self.TX_CELL_OPT, self.RX_CELL_OPT]
        if   cell_options == self.TX_CELL_OPT:
            our_cell_options = self.RX_CELL_OPT
        elif cell_options == self.RX_CELL_OPT:
            our_cell_options   = self.TX_CELL_OPT

        if (
                (
                    self._are_cells_allocated(
                        peerMac      = peerMac,
                        cell_list    = relocating_cells,
                        cell_options = our_cell_options
                    ) is True
                )
                and
                (num_cells <= len(candidate_cells))
            ):
            # find available cells in the received candidate cell list
            slots_in_slotframe = set(range(0, self.settings.tsch_slotframeLength))
            slots_in_use       = set(
                self.mote.tsch.get_busy_slots(self.SLOTFRAME_HANDLE_NEGOTIATED_CELLS)
            )
            candidate_slots    = set(
                [c[u'slotOffset'] for c in candidate_cells]
            )
            available_slots    = list(
                candidate_slots.intersection(
                    set(self._get_available_slots())
                )
            )

            code = d.SIXP_RC_SUCCESS
            cell_list = []
            if available_slots:
                # prepare response
                selected_slots = random.sample(available_slots, num_cells)
                for cell in candidate_cells:
                    if cell[u'slotOffset'] in selected_slots:
                        cell_list.append(cell)

                self._lock_cells(cell_list)
            else:
                # we will return an empty cell list with RC_SUCCESS
                pass

            # prepare callback
            def callback(event, packet):
                if event == d.SIXP_CALLBACK_EVENT_MAC_ACK_RECEPTION:
                    num_relocations = len(cell_list)
                    self._relocate_cells(
                        neighbor      = peerMac,
                        src_cell_list = relocating_cells[:num_relocations],
                        dst_cell_list = cell_list,
                        cell_options  = our_cell_options
                    )
                self._unlock_cells(cell_list)

        else:
            code      = d.SIXP_RC_ERR
            cell_list = None
            callback  = None

        # send a response
        self.mote.sixp.send_response(
            dstMac      = peerMac,
            return_code = code,
            cellList    = cell_list,
            callback    = callback
        )


    # CLEAR command related stuff
    def _receive_clear_request(self, request):

        peerMac = request[u'mac'][u'srcMac']

        def callback(event, packet):
            # remove all the cells no matter what happens
            self._clear_cells(peerMac)

        # create CLEAR response
        self.mote.sixp.send_response(
            dstMac      = peerMac,
            return_code = d.SIXP_RC_SUCCESS,
            callback    = callback
        )

    # autonomous cell
    def _compute_autonomous_cell(self, mac_addr):
        slotframe = self.mote.tsch.get_slotframe(
            self.SLOTFRAME_HANDLE_AUTONOMOUS_CELLS
        )
        hash_value = self._sax(mac_addr)

        slot_offset = int(1 + (hash_value % (slotframe.length - 1)))
        channel_offset = int(hash_value % self.settings.phy_numChans)
        
        # slot_offset=1;
        # channel_offset=10;
        print(slot_offset)
        print(channel_offset)

        return (slot_offset, channel_offset)

    # SAX
    def _sax(self, mac_addr):
        # XXX: a concrete definition of this hash function is needed to be
        # provided by the draft

        LEFT_SHIFT_NUM = 5
        RIGHT_SHIFT_NUM = 2

        # assuming v (seed) is 0
        hash_value = 0
        for word in netaddr.EUI(mac_addr).words:
            for byte in divmod(word, 0x100):
                left_shifted = (hash_value << LEFT_SHIFT_NUM)
                right_shifted = (hash_value >> RIGHT_SHIFT_NUM)
                hash_value ^= left_shifted + right_shifted + byte

        # assuming T (table size) is 16-bit
        return hash_value & 0xFFFF
