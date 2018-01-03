import matplotlib.pyplot as plt

def line_plot(x, y, x_label, y_label, title):
    plt.plot(x, y, '', linewidth=1, color='b')
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.title(title)
    plt.legend()
    plt.show()


