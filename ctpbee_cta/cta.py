"""
Notice : 神兽保佑 ，测试一次通过
//      
//      ┏┛ ┻━━━━━┛ ┻┓
//      ┃　　　　　　 ┃
//      ┃　　　━　　　┃
//      ┃　┳┛　  ┗┳　┃
//      ┃　　　　　　 ┃
//      ┃　　　┻　　　┃
//      ┃　　　　　　 ┃
//      ┗━┓　　　┏━━━┛
//        ┃　　　┃   Author: somewheve
//        ┃　　　┃   Datetime: 2019/7/7 上午11:08  ---> 无知即是罪恶
//        ┃　　　┗━━━━━━━━━┓
//        ┃　　　　　　　    ┣┓
//        ┃　　　　         ┏┛
//        ┗━┓ ┓ ┏━━━┳ ┓ ┏━┛
//          ┃ ┫ ┫   ┃ ┫ ┫
//          ┗━┻━┛   ┗━┻━┛
//
"""
from ctpbee import CtpBee
from ctpbee.ctp.constant import Direction, Offset, OrderRequest, OrderType, ContractData

from ctpbee.event_engine import Event
from ctpbee.ctp.constant import EVENT_LOG


def round_to(value: float, target: float):
    """
    Round price to price tick value.
    """
    rounded = int(round(value / target)) * target
    return rounded


class Cta:
    """"""

    author = ""
    parameters = []
    variables = []

    def __init__(self, symbol, vt_symbol, app: CtpBee):
        """"""
        self.symbol = symbol
        self.vt_symbol = vt_symbol
        self.inited = False
        self.trading = False
        self.pos = 0
        self.app = app
        self.offset_converter = OffsetConverter(self.main_engine)
        self.orderid_strategy_map = {}
        self.strategy_orderid_map = {}

    def write_log(self, info):
        log = Event(EVENT_LOG, info)
        self.app.event_engine.put(log)

    def core_send_order(
            self,
            contract: ContractData,
            direction: Direction,
            offset: Offset,
            price: float,
            volume: float,
            type: OrderType,
            lock: bool
    ):
        """
        发单到服务器
        """
        # Create request and send order.
        original_req = OrderRequest(
            symbol=contract.symbol,
            exchange=contract.exchange,
            direction=direction,
            offset=offset,
            type=type,
            price=price,
            volume=volume,
        )

        # Convert with offset converter
        req_list = self.offset_converter.convert_order_request(original_req, lock)
        # Send Orders
        vt_orderids = []

        for req in req_list:
            vt_orderid = self.app.send_order(req)
            vt_orderids.append(vt_orderid)
            self.offset_converter.update_order_request(req, vt_orderid)
        return vt_orderids

    def buy(self, price: float, volume: float, stop: bool = False, lock: bool = False):
        """
        Send buy order to open a long position.
        """

        return self.send_order(Direction.LONG, Offset.OPEN, price, volume, stop, lock)

    def sell(self, price: float, volume: float, stop: bool = False, lock: bool = False):
        """
        Send sell order to close a long position.
        """
        return self.send_order(Direction.SHORT, Offset.CLOSE, price, volume, stop, lock)

    def short(self, price: float, volume: float, stop: bool = False, lock: bool = False):
        """
        Send short order to open as short position.
        """
        return self.send_order(Direction.SHORT, Offset.OPEN, price, volume, stop, lock)

    def cover(self, price: float, volume: float, stop: bool = False, lock: bool = False):
        """
        Send cover order to close a short position.
        """
        return self.send_order(Direction.LONG, Offset.CLOSE, price, volume, stop, lock)

    def send_order(
            self,
            direction: Direction,
            offset: Offset,
            price: float,
            volume: float,
            stop: bool,
            lock: bool
    ):
        """
        """
        contract = self.app.recorder.get_contract()
        if not contract:
            self.write_log(f"委托失败，找不到合约：{contract.vt_symbol}")
            return ""

        # Round order price and volume to nearest incremental value
        price = round_to(price, contract.pricetick)
        volume = round_to(volume, contract.min_volume)

        if stop:
            if contract.stop_supported:
                return self.send_server_stop_order(strategy, contract, direction, offset, price, volume, lock)
            else:
                return self.send_local_stop_order(strategy, direction, offset, price, volume, lock)
        else:
            return self.send_limit_order(strategy, contract, direction, offset, price, volume, lock)
