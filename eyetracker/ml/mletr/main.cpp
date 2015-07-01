#include <QApplication>
#include <QQmlApplicationEngine>


//x = cos(t);
//y = sin(2*t) / 2;


int main(int argc, char * argv[])
{
    QApplication app(argc, argv);

    QQmlApplicationEngine engine;
    engine.load(QUrl(QStringLiteral("qrc:///main.qml")));

    return app.exec();
}
