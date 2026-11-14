class DomainError(Exception): pass
class InvalidPeriod(DomainError): pass
class OutsideWorkingHours(DomainError): pass
class BookingTooLong(DomainError): pass
class SeatAlreadyBooked(DomainError): pass